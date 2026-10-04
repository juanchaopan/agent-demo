from jsonpath_ng import parse
from pydantic import ValidationError
from graph.fields import missing_fields
from model import Event, Intent, State


def apply(data: dict, intent: Intent):
    path = parse(intent["path"])
    matches = path.find(data)
    if not matches:
        raise ValueError(f"{intent['path']} does not exist")
    value = intent.get("value")
    match intent["operation"]:
        case "set":
            path.update(data, value)
        case "add":
            path.update(data, [*(matches[0].value or []), value])
        case "remove":
            items = list(matches[0].value or [])
            items.pop(value)
            path.update(data, items)


def submit(event: Event, intents: list[Intent]) -> str | None:
    # Demo only: no downstream system exists, so passing the checks counts as submitted.
    if any(i.get("error") for i in intents if i["operation"] != "submit"):
        return "Not submitted: some edits in this message were rejected."
    if missing := missing_fields(event):
        return f"Not submitted: these fields are still missing: {missing}"
    return None


def execute_intents(state: State):
    event = state["event"]
    intents = state["intents"] or []
    for intent in intents:
        if intent.get("error") or intent["operation"] == "submit":
            continue
        data = event.model_dump()
        try:
            apply(data, intent)
            event = Event.model_validate(data)
        except ValidationError as e:
            intent["error"] = "; ".join(
                f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()
            )
        except Exception as e:  # pylint: disable=broad-except
            intent["error"] = str(e)
    for intent in intents:
        if intent["operation"] == "submit" and not intent.get("error"):
            intent["error"] = submit(event, intents)
    return {"event": event, "intents": intents}
