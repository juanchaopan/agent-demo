from json import dumps
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import model
from model import Event, Intent, State

SYSTEM_PROMPT = f"""
You help a user fill in an Event through conversation.
Read the user's LAST message and turn what it asks for into a list of intents.
Return an empty list if it asks for no change.

Event JSON schema:
{dumps(Event.model_json_schema())}

An intent has:
- path: JSONPath into the Event, e.g. $.title or $.awards[0].cashValue
- operation:
  - "set": replace the value at path, use null to clear it (or "" for an empty optional URL)
  - "add": append value to the list at path; for an award, fill the fields the user gave and use null for the rest
  - "remove": delete the item at index value from the list at path
  - "submit": the user explicitly confirms the Event is complete and asks to submit it; path is "$" and value is null.
    Never emit it just because all fields are filled, and not if the user wants more changes.
- value: the new value, matching the schema. Convert dates to ISO 8601.
- error: a short message if the user gave a value you cannot interpret (set value to null), otherwise null

Only emit changes the last message asks for, never repeat existing values.
Do not validate values, that is done afterwards.
"""



class Extraction(BaseModel):
    intents: list[Intent]


extractor = model.with_structured_output(Extraction, method="function_calling")


async def extract_semantics(state: State):
    current = state["event"].model_dump_json(indent=2)
    result = await extractor.ainvoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(content=f"{state['request']}\n\nCurrent Event:\n{current}"),
        ]
    )
    return {"intents": result.intents}
