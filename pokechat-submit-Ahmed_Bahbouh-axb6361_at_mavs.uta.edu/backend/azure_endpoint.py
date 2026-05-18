"""Normalize Azure OpenAI endpoint URLs for the official Python SDK."""

from urllib.parse import urlparse


def normalize_azure_openai_endpoint(endpoint: str) -> str:
    """
    AzureOpenAI(azure_endpoint=...) must be the resource base URL only, e.g.
    https://your-name.openai.azure.com/

    Values copied from REST docs (…/openai/v1/chat/completions) make the SDK
    build a bad URL and Azure returns 404 Resource not found.
    """
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return endpoint
    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/"
    return endpoint if endpoint.endswith("/") else f"{endpoint}/"
