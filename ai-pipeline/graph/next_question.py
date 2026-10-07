from model import Award, Event
from graph.fields import missing_fields

QUESTIONS = {
    "title": "What is the title of the event?",
    "description": "What is the description of the event?",
    "openRegistrationDate": "When does the registration open?",
    "closeRegistrationDate": "When does the registration close?",
    "openSubmissionDate": "When does the submission open?",
    "closeSubmissionDate": "When does the submission close?",
    "openFinalizeDate": "When does the finalization open?",
    "closeFinalizeDate": "When does the finalization close?",
    "bannerImageUrl": "What is the URL for the event's banner image?",
    "videoUrl": "What is the URL for the event's video?",
    "registrationFormUrl": "What is the URL for the event's registration form?",
    "submissionFormUrl": "What is the URL for the event's submission form?",
    "awards": "Would you like to add any awards for this event?",
    "editStatus": "Should the event be saved as a draft, published, or archived?",
}
AWARD_QUESTIONS = {
    "title": "What is the name of the award?",
    "description": "What is the description of {award}?",
    "number": "How many winners will there be for {award}?",
    "cashValue": "What is the cash value of {award}?",
    "descriptionUrl": "What is the URL of the page describing {award}?",
    "titleImageUrl": "What is the URL for the title image of {award}?",
}


def all_paths(event: Event) -> list[str]:
    paths = []
    for name in Event.model_fields:
        if name != "awards":
            paths.append(f"$.{name}")
        elif event.awards is None:
            paths.append("$.awards")
        else:
            paths += [
                f"$.awards[{i}].{field}"
                for i in range(len(event.awards))
                for field in Award.model_fields
            ]
    return paths


def question(event: Event, path: str) -> str:
    if path.startswith("$.awards["):
        i, field = path.removeprefix("$.awards[").split("].")
        title = event.awards[int(i)].title
        return AWARD_QUESTIONS[field].format(
            award=f'the "{title}" award' if title else "the award"
        )
    return QUESTIONS[path.removeprefix("$.")]


def next_question(event: Event, asked: str, intents: list) -> str:
    # asked: the field path the last question was about, or "add awards",
    # "another award", "submit", "" (see the extract_semantics prompt).
    order, missing = all_paths(event), set(missing_fields(event))
    awards = event.awards or []
    if awards and asked == f"$.awards[{len(awards) - 1}].titleImageUrl":
        return "Would you like to add another award?"
    if asked == "another award" and any(i["operation"] == "add" for i in intents):
        return question(event, f"$.awards[{len(awards) - 1}].title")
    if asked in ("add awards", "another award"):
        # continue from where the awards sit in the order
        start = (
            order.index("$.submissionFormUrl")
            if asked == "add awards"
            else order.index("$.editStatus") - 1
        )
    else:
        start = order.index(asked) if asked in order else -1
    later = [p for p in order[start + 1 :] if p in missing]
    if later:
        return question(event, later[0])
    earlier = [p for p in order[: start + 1] if p in missing and p != asked]
    if earlier:
        return question(event, earlier[0])
    if asked in missing:
        return f"{question(event, asked)} If there isn't one, just say none; it is the last thing needed."
    return "Here is the complete Event: {the whole Event}. Shall I submit it now?"
