from functools import cache
from os import getenv
from pymongo import MongoClient
from model import Conversation


@cache
def mongo_client() -> MongoClient:
    ca_file = getenv("DB_CA")
    return MongoClient(
        host=getenv("MONGO_HOST"),
        port=int(getenv("MONGO_PORT", "27017")),
        username=getenv("MONGO_DB_USERNAME"),
        password=getenv("MONGO_DB_PASSWORD"),
        authSource=getenv("MONGO_DB"),
        tls=ca_file is not None,
        tlsCAFile=ca_file,
    )


class ConversationStore:
    def __init__(self, client: MongoClient | None = None):
        client = client or mongo_client()
        self.conversations = client.get_database(getenv("MONGO_DB"))["conversations"]

    def get(self, conversation_id: str) -> Conversation | None:
        doc = self.conversations.find_one({"_id": conversation_id})
        return Conversation.model_validate(doc) if doc else None

    def complete_message(self, conversation_id: str, message_id: str, content: str, event):
        """Fill in the assistant message and save the updated event in one write."""
        result = self.conversations.update_one(
            {"_id": conversation_id},
            {
                "$set": {
                    "messages.$[m].status": "processed",
                    "messages.$[m].content": content,
                    "event": event.model_dump(),
                }
            },
            array_filters=[{"m._id": message_id}],
        )
        if result.matched_count == 0:
            raise LookupError(f"Conversation {conversation_id} not found")

    def fail_message(self, conversation_id: str, message_id: str):
        self.conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"messages.$[m].status": "failed"}},
            array_filters=[{"m._id": message_id}],
        )
