from functools import cache
from os import environ, getenv
from pymongo import MongoClient
from model import Conversation, Message


@cache
def mongo_client() -> MongoClient:
    ca_file = getenv("DB_CA")
    return MongoClient(
        host=environ["MONGO_HOST"],
        port=int(getenv("MONGO_PORT", "27017")),
        username=getenv("MONGO_DB_USERNAME"),
        password=getenv("MONGO_DB_PASSWORD"),
        authSource=environ["MONGO_DB"],
        tls=ca_file is not None,
        tlsCAFile=ca_file,
    )


class ConversationStore:
    """Conversations as the HTTP side sees them: create, read, append.

    The AI worker owns the pending -> processed/failed transition of assistant
    messages; this side only ever inserts them as pending.
    """

    def __init__(self, client: MongoClient | None = None):
        client = client or mongo_client()
        self.conversations = client.get_database(environ["MONGO_DB"])["conversations"]

    def create(self, conversation: Conversation):
        self.conversations.insert_one(conversation.model_dump(by_alias=True))

    def get(self, conversation_id: str) -> Conversation | None:
        doc = self.conversations.find_one({"_id": conversation_id})
        return Conversation.model_validate(doc) if doc else None

    def messages(
        self, conversation_id: str, start_message_id: str | None = None
    ) -> list[Message] | None:
        """Messages of a conversation, or None if it does not exist.

        With start_message_id, returns that message and everything after it, so a
        client can resume where it left off. An unknown id returns all messages.
        """
        doc = self.conversations.find_one({"_id": conversation_id}, {"messages": 1})
        if doc is None:
            return None
        messages = [Message.model_validate(m) for m in doc.get("messages", [])]
        start = next((i for i, m in enumerate(messages) if m.id == start_message_id), 0)
        return messages[start:]

    def append_messages(self, conversation_id: str, messages: list[Message]):
        """Add messages to the end of a conversation in one write."""
        result = self.conversations.update_one(
            {"_id": conversation_id},
            {
                "$push": {
                    "messages": {"$each": [m.model_dump(by_alias=True) for m in messages]}
                }
            },
        )
        if result.matched_count == 0:
            raise LookupError(f"Conversation {conversation_id} not found")

    def fail_message(self, conversation_id: str, message_id: str):
        self.conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"messages.$[m].status": "failed"}},
            array_filters=[{"m._id": message_id}],
        )
