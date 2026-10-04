from json import dumps
from bson import ObjectId
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from database import Activity, Chunk, ConversationStore, TokenStreamError, token_stream
from messaging import enqueue_message
from model import Conversation, Event, Message

app = FastAPI()
store = ConversationStore()


def new_exchange(content: str) -> tuple[Message, Message]:
    """A user message and the pending assistant message that will answer it."""
    user = Message(
        _id=str(ObjectId()),
        status="processed",
        role="user",
        content=content,
        activity=None,
    )
    assistant = Message(
        _id=str(ObjectId()),
        status="pending",
        role="assistant",
        content=None,
        activity=None,
    )
    return user, assistant


async def dispatch(conversation_id: str, assistant: Message):
    """Open the reply stream, then hand the pending message to the worker."""
    async with token_stream(assistant.id) as stream:
        await stream.open()
    try:
        await run_in_threadpool(enqueue_message, conversation_id, assistant.id)
    except Exception as error:
        # Nothing will ever process it, so don't leave it pending.
        await run_in_threadpool(store.fail_message, conversation_id, assistant.id)
        raise HTTPException(503, "Could not queue the message") from error


def sse(data: dict, event: str | None = None) -> str:
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {dumps(data)}\n\n"


@app.post("/conversations")
async def post_conversation():
    user, assistant = new_exchange("Let's create an event.")
    conversation = Conversation(
        _id=str(ObjectId()), messages=[user, assistant], event=Event()
    )
    await run_in_threadpool(store.create, conversation)
    await dispatch(conversation.id, assistant)
    return {"conversation_id": conversation.id}


@app.post("/conversations/{conversation_id}/messages")
async def post_message(
    conversation_id: str,
    content: str = Body(..., media_type="text/plain", min_length=1),
):
    user, assistant = new_exchange(content)
    try:
        await run_in_threadpool(
            store.append_messages, conversation_id, [user, assistant]
        )
    except LookupError as error:
        raise HTTPException(404, "Conversation not found") from error
    await dispatch(conversation_id, assistant)
    return {"message_id": user.id}


@app.get("/conversations/{conversation_id}/event")
async def get_event(conversation_id: str):
    conversation = await run_in_threadpool(store.get, conversation_id)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")
    return conversation.event


@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, start_message_id: str | None = Query(None)):
    """Server-sent events, one per finished message part or pending token:

    - default event, {message_id, role, content}: a finished message's content,
      or a piece of a pending one's.
    - `activity` event, {message_id, role, items}: an assistant message's
      activity items.
    - `error` event, {message_id, role}: the message failed or could not be
      read; if it was pending, the response ends here.
    """
    messages = await run_in_threadpool(store.messages, conversation_id, start_message_id)
    if messages is None:
        raise HTTPException(404, "Conversation not found")

    async def stream():
        for message in messages:
            head = {"message_id": message.id, "role": message.role}
            match message.status:
                case "processed":
                    if message.role == "assistant":
                        yield sse({**head, "items": message.activity}, event="activity")
                    yield sse({**head, "content": message.content})
                case "failed":
                    yield sse(head, event="error")
                case "pending":
                    try:
                        async with token_stream(message.id) as tokens:
                            async for frame in tokens.read():
                                match frame:
                                    case Chunk(text):
                                        yield sse({**head, "content": text})
                                    case Activity(items):
                                        yield sse({**head, "items": items}, event="activity")
                    except (TokenStreamError, TimeoutError, ValueError):
                        yield sse(head, event="error")
                        return

    return StreamingResponse(stream(), media_type="text/event-stream")
