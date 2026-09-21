from os import getenv
from pydantic import SecretStr
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model=getenv("LANGUAGE_MODEL", ""),
    base_url=getenv("LANGUAGE_MODEL_BASE_URL", ""),
    api_key=SecretStr(getenv("LANGUAGE_MODEL_API_KEY", "")),
)
