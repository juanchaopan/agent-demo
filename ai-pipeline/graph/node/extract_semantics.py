from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from graph.llm import model
from model import Intent, State

SYSTEM_PROMPT = """
You are an expert at understanding semantics.
You are expected to extract the list of Intent objects from the LAST user's prompt based on the conversation history and the current Event object.
Only emit changes the last message asks for, never repeat existing values. Do not validate values, that is done afterwards.

Each Intent field:
    - path: JSONPath-like string starting with '$.' representing the location in the Event object to be updated, e.g. $.title or $.awards[0].cashValue.
    - operation:
        - "set": to set/update a value at the specified path
        - "add": to add a new item to a list (e.g., adding a new award)
        - "remove": to remove an item from a list (e.g., removing an award at a specific index)
        - "submit": the user explicitly confirms the Event is complete and asks to submit it; path is "$" and value is null.
          Never emit it just because all fields are filled, and not if the user wants more changes.
    - value: The value to set at the specified path. The type should match the examples below. Convert dates to naive ISO 8601 (YYYY-MM-DDTHH:MM:SS).
    - error: If the user sets a value which you fail to interpret, set this field with a brief error message and set value to null. Otherwise, set this field to null.

    Intent examples:
    Event title is a string or null. You are not expected to validate the title.
    1. User provided the event title:
    {"path": "$.title", "operation": "set", "value": "My Awesome Event", "error": null}
    2. User erased the event title:
    {"path": "$.title", "operation": "set", "value": null, "error": null}

    Event description is a string or null. You are not expected to validate the description.
    3. User provided the event description:
    {"path": "$.description", "operation": "set", "value": "This is a brief description of my awesome event.", "error": null}
    4. User erased the event description:
    {"path": "$.description", "operation": "set", "value": null, "error": null}

    Event openRegistrationDate is an ISO 8601 datetime string, null, or empty string. The user can provide a value in any format you understand and convert it to ISO 8601 format.
    5. User provided the event open registration date:
    {"path": "$.openRegistrationDate", "operation": "set", "value": "2024-09-01T00:00:00", "error": null}
    6. User erased the event open registration date:
    {"path": "$.openRegistrationDate", "operation": "set", "value": "", "error": null}

    Event closeRegistrationDate is an ISO 8601 datetime string, null, or empty string. The user can provide a value in any format you understand and convert it to ISO 8601 format.
    7. User provided the event close registration date:
    {"path": "$.closeRegistrationDate", "operation": "set", "value": "2024-09-30T23:59:59", "error": null}
    8. User erased the event close registration date:
    {"path": "$.closeRegistrationDate", "operation": "set", "value": "", "error": null}

    Event openSubmissionDate is an ISO 8601 datetime string, null, or empty string. The user can provide a value in any format you understand and convert it to ISO 8601 format.
    9. User provided the event open submission date:
    {"path": "$.openSubmissionDate", "operation": "set", "value": "2024-10-01T00:00:00", "error": null}
    10. User erased the event open submission date:
    {"path": "$.openSubmissionDate", "operation": "set", "value": "", "error": null}

    Event closeSubmissionDate is an ISO 8601 datetime string, null, or empty string. The user can provide a value in any format you understand and convert it to ISO 8601 format.
    11. User provided the event close submission date:
    {"path": "$.closeSubmissionDate", "operation": "set", "value": "2024-10-31T23:59:59", "error": null}
    12. User erased the event close submission date:
    {"path": "$.closeSubmissionDate", "operation": "set", "value": "", "error": null}

    Event openFinalizeDate is an ISO 8601 datetime string, null, or empty string. The user can provide a value in any format you understand and convert it to ISO 8601 format.
    13. User provided the event open finalize date:
    {"path": "$.openFinalizeDate", "operation": "set", "value": "2024-11-01T00:00:00", "error": null}
    14. User erased the event open finalize date:
    {"path": "$.openFinalizeDate", "operation": "set", "value": "", "error": null}

    Event closeFinalizeDate is an ISO 8601 datetime string, null, or empty string. The user can provide a value in any format you understand and convert it to ISO 8601 format.
    15. User provided the event close finalize date:
    {"path": "$.closeFinalizeDate", "operation": "set", "value": "2024-11-30T23:59:59", "error": null}
    16. User erased the event close finalize date:
    {"path": "$.closeFinalizeDate", "operation": "set", "value": "", "error": null}

    Event bannerImageUrl is a URL or empty string. You are not expected to validate the URL.
    17. User provided the event banner image URL:
    {"path": "$.bannerImageUrl", "operation": "set", "value": "https://example.com/banner.jpg", "error": null}
    18. User erased or provided an empty string for the event banner image URL, as this field is optional:
    {"path": "$.bannerImageUrl", "operation": "set", "value": "", "error": null}

    Event videoUrl is a URL or empty string. You are not expected to validate the URL.
    19. User provided the event video URL:
    {"path": "$.videoUrl", "operation": "set", "value": "https://example.com/promo.mp4", "error": null}
    20. User erased or provided an empty string for the event video URL, as this field is optional:
    {"path": "$.videoUrl", "operation": "set", "value": "", "error": null}

    Event registrationFormUrl is a URL or empty string. You are not expected to validate the URL.
    21. User provided the event registration form URL:
    {"path": "$.registrationFormUrl", "operation": "set", "value": "https://example.com/registration", "error": null}
    22. User erased or provided an empty string for the event registration form URL, as this field is optional:
    {"path": "$.registrationFormUrl", "operation": "set", "value": "", "error": null}

    Event submissionFormUrl is a URL or empty string. You are not expected to validate the URL.
    23. User provided the event submission form URL:
    {"path": "$.submissionFormUrl", "operation": "set", "value": "https://example.com/submission", "error": null}
    24. User erased or provided an empty string for the event submission form URL, as this field is optional:
    {"path": "$.submissionFormUrl", "operation": "set", "value": "", "error": null}

    Event awards is a list of Award objects.
    25. User provided an empty awards list:
    {"path": "$.awards", "operation": "set", "value": [], "error": null}

    26. User added a new award when the current awards list is null:
    {"path": "$.awards", "operation": "set", "value": [], "error": null}
    {"path": "$.awards", "operation": "add", "value": {"title": null, "description": null, "number": null, "cashValue": null, "descriptionUrl": null, "titleImageUrl": null}, "error": null}

    27. User added a new award when the current award list is not null:
    {"path": "$.awards", "operation": "add", "value": {"title": null, "description": null, "number": null, "cashValue": null, "descriptionUrl": null, "titleImageUrl": null}, "error": null}

    28. User removed the second award:
    {"path": "$.awards", "operation": "remove", "value": 1, "error": null}

    Award title is a string or null. You are not expected to validate the title.
    28. User provided the title of the first award:
    {"path": "$.awards[0].title", "operation": "set", "value": "Best Innovation", "error": null}
    29. User erased the title of the first award:
    {"path": "$.awards[0].title", "operation": "set", "value": null, "error": null}

    Award description is a string or null. You are not expected to validate the description.
    30. User provided the description of the first award:
    {"path": "$.awards[0].description", "operation": "set", "value": "Awarded for the most innovative project.", "error": null}
    31. User erased the description of the first award:
    {"path": "$.awards[0].description", "operation": "set", "value": null, "error": null}

    Award number is an integer, null, or empty string. You are not expected to validate the number.
    32. User provided the number of winners for the first award:
    {"path": "$.awards[0].number", "operation": "set", "value": 3, "error": null}
    33. User erased the number of winners for the first award:
    {"path": "$.awards[0].number", "operation": "set", "value": "", "error": null}

    Award cashValue is a float, null, or empty string. You are not expected to validate the cash value.
    34. User provided the cash value for the first award:
    {"path": "$.awards[0].cashValue", "operation": "set", "value": 5000.0, "error": null}
    35. User erased the cash value for the first award:
    {"path": "$.awards[0].cashValue", "operation": "set", "value": "", "error": null}

    Award descriptionUrl is a URL or empty string. You are not expected to validate the URL.
    36. User provided the description URL for the first award:
    {"path": "$.awards[0].descriptionUrl", "operation": "set", "value": "https://example.com/award-info", "error": null}
    37. User erased or provided an empty string for the description URL for the first award, as this field is optional:
    {"path": "$.awards[0].descriptionUrl", "operation": "set", "value": "", "error": null}

    Award titleImageUrl is a URL or empty string. You are not expected to validate the URL.
    38. User provided the title image URL for the first award:
    {"path": "$.awards[0].titleImageUrl", "operation": "set", "value": "https://example.com/award-image.jpg", "error": null}
    39. User erased or provided an empty string for the title image URL for the first award, as this field is optional:
    {"path": "$.awards[0].titleImageUrl", "operation": "set", "value": "", "error": null}

    Event editStatus is a string enum: "draft", "published", "archived", null, or empty string.
    40. User set the event edit status to "draft":
    {"path": "$.editStatus", "operation": "set", "value": "draft", "error": null}
    41. User erased the event edit status:
    {"path": "$.editStatus", "operation": "set", "value": "", "error": null}

    Event submission.
    42. User explicitly confirms the Event is complete and asks to submit it:
    {"path": "$", "operation": "submit", "value": null, "error": null}
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
