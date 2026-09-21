from asyncio import new_event_loop
from os import getenv
from urllib.parse import quote
from celery import Celery
from langchain_core.messages import AIMessage, HumanMessage
from database import ConversationStore, token_stream
from graph import build_graph

app = Celery(
    "ai-pipeline",
    broker="amqp://{user}:{password}@{host}:{port}//".format(
        user=quote(getenv("RABBITMQ_USER", ""), safe=""),
        password=quote(getenv("RABBITMQ_PASSWORD", ""), safe=""),
        host=getenv("RABBITMQ_HOST"),
        port=getenv("RABBITMQ_PORT", "5672"),
    ),
    broker_transport_options={"confirm_publish": True},
    task_default_exchange_type="topic",
    task_default_queue_type="quorum",
    control_queue_exclusive=True,
    event_queue_exclusive=True,
)

graph = build_graph()
store = ConversationStore()
loop = None


def run(coroutine):
    # The LLM client keeps connections tied to the loop it first ran on,
    # so every task in a worker process has to share one loop.
    global loop
    if loop is None:
        loop = new_event_loop()
    return loop.run_until_complete(coroutine)


async def answer(conversation_id: str, message_id: str, state: dict):
    async with token_stream(message_id) as stream:
        try:
            final = None
            async for mode, data in graph.astream(
                state, stream_mode=["messages", "values"]
            ):
                if mode == "values":
                    final = data
                    continue
                chunk, metadata = data
                if "generate_verbose" in metadata.get("tags", []) and chunk.text:
                    await stream.chunk(chunk.text)
            store.complete_message(
                conversation_id, message_id, final["response"], final["event"]
            )
        except Exception:
            store.fail_message(conversation_id, message_id)
            await stream.fail()
            raise
        # Only after the message is saved, so a client that sees "end" can read it.
        await stream.end()


@app.task(name="process_message")
def process_message(conversation_id: str, message_id: str):
    conversation = store.get(conversation_id)
    if conversation is None:
        raise LookupError(f"Conversation {conversation_id} not found")

    position = next(
        (i for i, m in enumerate(conversation.messages) if m.id == message_id), None
    )
    if position is None:
        raise LookupError(f"Message {message_id} not found")
    if conversation.messages[position].status == "processed":
        return  # redelivered after it already finished

    history = [m for m in conversation.messages[:position] if m.status == "processed"]
    if not history or history[-1].role != "user":
        raise ValueError(f"No user message to answer before {message_id}")
    *history, request = history

    state = {
        "messages": [
            (AIMessage if m.role == "assistant" else HumanMessage)(content=m.content)
            for m in history
        ],
        "event": conversation.event,
        "request": request.content,
        "intents": None,
        "response": None,
    }
    run(answer(conversation_id, message_id, state))
