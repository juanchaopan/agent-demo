from json import dumps
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import model
from graph.next_question import next_question
from model import State

SYSTEM_PROMPT = """
You help a user create an Event through chat: ask for one thing at a time, answer their questions and propose values when asked.

Input: each turn you get the user's message, the intents extracted from it (already applied; one with an error did not take effect), the current Event and the next question (already decided for you). The Event has not been submitted; never say it was.

Reply by the first rule that fits, judging by what the user means, not their wording:
1. An intent with an error: say briefly in plain words what did not take effect and why, then ask that field again.
2. The user asked you to suggest a value: propose one concrete value that fits the Event and ask "How about: "{value}"? Would you like to use it, or something else?"
3. The user only asked a question: answer it briefly, then ask your last question again, not the next question.
4. The user wants a specific field: ask it.
5. Your last message asked whether to submit and the user said no: ask what they would like to change.
6. Otherwise ask exactly the next question from the input, filling in anything in braces; nothing else. Never decide on your own that the Event is complete.

How to reply:
- Ask for a value with a what / when / how many question, so "no" can only mean the thing does not exist. Yes/no questions are only for adding awards, submitting and accepting a suggestion.
- Use plain words, never field names or a required format. Keep replies short.
- The user already sees this turn's changes; never repeat or list them.
- When showing the whole Event, list every field readably and write "none" for "".
"""


async def generate_verbose(state: State):
    event = state["event"]
    intents = state["intents"] or []
    if any(i["operation"] == "submit" and not i.get("error") for i in intents):
        return {"response": "The event was submitted."}
    result = await model.ainvoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(
                content=f"{state['request']}\n\n"
                f"Intents:\n{dumps(state['intents'])}\n\n"
                f"Current Event:\n{event.model_dump_json(indent=2)}\n\n"
                f"Next question: {next_question(event, state['asked'] or '', intents)}"
            ),
        ]
    )
    return {"response": result.text}
