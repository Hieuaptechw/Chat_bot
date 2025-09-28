import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Lấy API Key từ biến môi trường
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Vui lòng đặt biến môi trường OPENAI_API_KEY trước khi chạy app!")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENAI_API_KEY
)

@app.route("/api/quiz", methods=["POST"])
def quiz_proxy():
    data = request.json
    question = data.get("question", "")
    options = data.get("options", [])
    multi_answer = data.get("multi_answer", False)

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])

    if multi_answer:
        prompt = f"""
Question: {question}
Options:
{options_text}

Instruction: Reply with ONLY the number(s) of the correct option(s), separated by commas if multiple. Do NOT include explanations.
Example: 1,3
"""
    else:
        prompt = f"""
Question: {question}
Options:
{options_text}

Instruction: Reply with ONLY the number of the correct option. Do NOT include explanations.
Example: 2
"""

    completion = client.chat.completions.create(
        model="x-ai/grok-4-fast:free",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = ""
    choice = completion.choices[0]

    if hasattr(choice, "message") and choice.message and hasattr(choice.message, "content"):
        answer = choice.message.content.strip()
    elif hasattr(choice, "content"):
        answer = choice.content.strip()

    if multi_answer:
        answer_list = [a.strip() for a in answer.split(",") if a.strip().isdigit()]
    else:
        answer_list = [answer] if answer else []

    return jsonify({"answer": answer_list or ["AI did not return a valid answer."]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Lấy API Key từ biến môi trường
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Vui lòng đặt biến môi trường OPENAI_API_KEY trước khi chạy app!")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENAI_API_KEY
)

@app.route("/api/quiz", methods=["POST"])
def quiz_proxy():
    data = request.json
    question = data.get("question", "")
    options = data.get("options", [])
    multi_answer = data.get("multi_answer", False)

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])

    if multi_answer:
        prompt = f"""
Question: {question}
Options:
{options_text}

Instruction: Reply with ONLY the number(s) of the correct option(s), separated by commas if multiple. Do NOT include explanations.
Example: 1,3
"""
    else:
        prompt = f"""
Question: {question}
Options:
{options_text}

Instruction: Reply with ONLY the number of the correct option. Do NOT include explanations.
Example: 2
"""

    completion = client.chat.completions.create(
        model="x-ai/grok-4-fast:free",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = ""
    choice = completion.choices[0]

    if hasattr(choice, "message") and choice.message and hasattr(choice.message, "content"):
        answer = choice.message.content.strip()
    elif hasattr(choice, "content"):
        answer = choice.content.strip()

    if multi_answer:
        answer_list = [a.strip() for a in answer.split(",") if a.strip().isdigit()]
    else:
        answer_list = [answer] if answer else []

    return jsonify({"answer": answer_list or ["AI did not return a valid answer."]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
