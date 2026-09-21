from json import dumps
from langchain_core.messages import HumanMessage, SystemMessage
from graph.fields import missing_fields
from graph.llm import model
from model import State

SYSTEM_PROMPT = """
You guide a user through creating an Event, one question at a time.
You receive the user's last message, the edits applied to the Event (intents),
the current Event, and the paths of the fields that are still missing, in order.

1. Briefly say what was updated. If an intent has an error, it was rejected:
   explain why and what a valid value looks like.
2. Then ask for the next missing field, one question only, or the field the user asked to jump to.
   A missing award field is asked for that award, and once an award is complete ask if they want to add another.
3. If nothing is missing, show the whole Event in a readable format and ask if they have final changes.

An intent with operation "submit" is a request to submit the Event.
If it has no error, the Event was submitted: say so and stop, do not ask anything else.
If it has an error, the Event was not submitted: explain why and continue from step 2.

Answer any question the user asked. Keep it short.
"""

llm = model.with_config(tags=["generate_verbose"])


async def generate_verbose(state: State):
    event = state["event"]
    result = await llm.ainvoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(
                content=f"{state['request']}\n\n"
                f"Intents:\n{dumps(state['intents'])}\n\n"
                f"Missing fields:\n{dumps(missing_fields(event))}\n\n"
                f"Current Event:\n{event.model_dump_json(indent=2)}"
            ),
        ]
    )
    return {"response": result.text}
