from os import getenv
from urllib.parse import quote
from celery import Celery

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
)


def enqueue_message(conversation_id: str, message_id: str):
    """Queue the pending assistant message for the AI worker.

    Blocks until the broker confirms, so call it from a threadpool in async
    endpoints. Raises if the broker is unreachable; nothing will process the
    message then, so the caller should mark it failed.
    """
    app.send_task("process_message", args=[conversation_id, message_id])
