import json
import os
from pathlib import Path

from azure_endpoint import normalize_azure_openai_endpoint
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_raw_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
_azure_endpoint = normalize_azure_openai_endpoint(_raw_endpoint) if _raw_endpoint else None
_azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "OurCS35")

if not _azure_endpoint or not _azure_key:
    raise RuntimeError(
        "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in a .env file "
        "(see .env.example in the project root)."
    )

client = AzureOpenAI(
    azure_endpoint=_azure_endpoint,
    api_key=_azure_key,
    api_version=_api_version,
)
message_text = [
	{
		"role": "system",
		"content": "You are a backend API and respond to queries with JSON messages. You only respond with an array of JSON objects."
	},
	{
		"role": "user",
		"content": "Strongest pokemon"
	},
	{
		"role": "assistant",
		"content": "[\n{\n\"name\": \"Arceus\",\n\"id\": 493\n},\n{\n\"name\": \"Mewtwo\",\n\"id\": 150\n}]"
	},
    {"role": "user", "content": "weakest pokemon; limit 1"}
]
completion = client.chat.completions.create(
    model=_deployment,
    messages=message_text,
    max_completion_tokens=800,
)

print(json.loads(completion.choices[0].message.content))