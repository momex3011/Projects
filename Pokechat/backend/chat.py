from pathlib import Path

from azure_endpoint import normalize_azure_openai_endpoint
from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from openai import AzureOpenAI
import json, os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)
CORS(app)

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

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        return res

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/chat/hello', methods=['GET'])
def hello():
    return "Hello, World!"

@app.route('/chat/query', methods=['GET'])
def strongest():
    query = request.args.get('q', 'ditto limit 1')
    print(query)
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
        {"role": "user", "content": f"{query}"}
    ]

    try:
        # Some Azure models only allow default temperature (1) and reject extra sampling params.
        completion = client.chat.completions.create(
            model=_deployment,
            messages=message_text,
            max_completion_tokens=800,
        )

        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", "3001"))
    debug_enabled = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_enabled, use_reloader=debug_enabled)
