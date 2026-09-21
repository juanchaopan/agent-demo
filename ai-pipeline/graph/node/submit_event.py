from httpx import AsyncClient
from graph.fields import missing_fields
from model import State

EVENT_API_URL = "http://app:3000/api/events"


async def submit_event(state: State):
    intents = state["intents"] or []
    submit = next((i for i in intents if i["operation"] == "submit"), None)
    if submit is None or submit.get("error"):
        return {}

    event = state["event"]
    missing = missing_fields(event)
    if any(i.get("error") for i in intents if i is not submit):
        submit["error"] = "Not submitted: some edits in this message were rejected."
    elif missing:
        submit["error"] = f"Not submitted: these fields are still missing: {missing}"
    else:
        try:
            async with AsyncClient(timeout=5) as client:
                response = await client.post(
                    EVENT_API_URL, json=event.model_dump(mode="json")
                )
                response.raise_for_status()
        except Exception as e:  # pylint: disable=broad-except
            submit["error"] = f"Not submitted: {e}"
    return {"intents": intents}
