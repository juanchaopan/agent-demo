from json import dumps
from bson import ObjectId
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from database import ConversationStore, TokenStreamError, token_stream
from messaging import enqueue_message
from model import Conversation, Event, Message

app = FastAPI()
store = ConversationStore()


def new_exchange(content: str) -> tuple[Message, Message]:
    """A user message and the pending assistant message that will answer it."""
    user = Message(
        _id=str(ObjectId()), status="processed", role="user", content=content
    )
    assistant = Message(
        _id=str(ObjectId()), status="pending", role="assistant", content=None
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


@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, start_message_id: str | None = Query(None)):
    """Server-sent events: finished messages whole, pending ones token by token.

    A message the worker failed on is reported as an `error` event. If a pending
    message's stream fails or dries up, the response ends after its `error`.
    """
    messages = await run_in_threadpool(store.messages, conversation_id, start_message_id)
    if messages is None:
        raise HTTPException(404, "Conversation not found")

    async def stream():
        for message in messages:
            head = {"message_id": message.id, "role": message.role}
            match message.status:
                case "processed":
                    yield sse({**head, "content": message.content})
                case "failed":
                    yield sse(head, event="error")
                case "pending":
                    try:
                        async with token_stream(message.id) as tokens:
                            async for chunk in tokens.read():
                                yield sse({**head, "content": chunk})
                    except (TokenStreamError, TimeoutError):
                        yield sse(head, event="error")
                        return

    return StreamingResponse(stream(), media_type="text/event-stream")
