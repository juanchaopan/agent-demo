from model import State


def build_activity(state: State):
    return {
        "activity": [
            {
                "field": "" if intent["path"] == "$" else intent["path"].removeprefix("$."),
                "operation": intent["operation"],
                "value": intent.get("value"),
                "status": "rejected" if intent.get("error") else "applied",
                "error": intent.get("error"),
            }
            for intent in state["intents"] or []
        ]
    }
