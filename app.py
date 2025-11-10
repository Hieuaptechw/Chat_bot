from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 🧩 Thêm dòng này
from pydantic import BaseModel, Field
from typing import List
import boto3
import json
import re, os

# ================== CONFIG ==================
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_REGION = "ap-southeast-1"
CLAUDE_ARN = "arn:aws:bedrock:ap-southeast-1:692957432909:inference-profile/apac.anthropic.claude-sonnet-4-20250514-v1:0"

app = FastAPI(title="Quiz API", version="2.0.0")

# ================== 🔐 CORS FIX ==================
# Cho phép gọi từ mọi origin (bao gồm cả file:// hoặc Chrome extension)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 👈 Cho phép tất cả domain (hoặc chỉnh cụ thể)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =================================================

# Initialize Bedrock client
bedrock_rt = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)


class QuizRequest(BaseModel):
    question: str = Field(..., description="Câu hỏi trắc nghiệm")
    options: List[str] = Field(..., description="Danh sách các đáp án", min_length=2)
    multi_answer: bool = Field(False, description="Cho phép nhiều câu trả lời đúng")

class QuizResponse(BaseModel):
    question: str
    options: List[str]
    answer_indices: List[int] = Field(..., description="Mảng số thứ tự các câu trả lời đúng (bắt đầu từ 1)")
    explanation: str


@app.get("/")
def root():
    return {
        "status": "online",
        "model": "Claude Sonnet 4",
        "endpoint": "POST /answer"
    }


@app.post("/answer", response_model=QuizResponse)
def answer_quiz(request: QuizRequest):
    # Tạo prompt
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(request.options)])
    if request.multi_answer:
        instruction = "Reply with ALL correct option numbers (1, 2, 3, etc.) separated by commas."
    else:
        instruction = "Reply with ONLY ONE correct option number (1, 2, 3, etc.)."

    prompt = f"""Answer this multiple choice question. {instruction}

Question: {request.question}

Options:
{options_text}

Format your answer exactly as:
Answer: [NUMBER(S)]
Explanation: [brief explanation]

Examples:
- Single answer: "Answer: 2"
- Multiple answers: "Answer: 1, 3, 4"
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.1,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
    }

    try:
        response = bedrock_rt.invoke_model(
            modelId=CLAUDE_ARN,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json"
        )

        result = json.loads(response["body"].read())

        response_text = ""
        if "content" in result:
            for item in result["content"]:
                if item["type"] == "text":
                    response_text = item["text"]
                    break

        # Parse answer & explanation
        answer_indices = []
        explanation = ""
        lines = response_text.strip().split("\n")
        for line in lines:
            if line.startswith("Answer:"):
                answer_str = line.replace("Answer:", "").strip()
                numbers = re.findall(r'\d+', answer_str)
                answer_indices = [int(n) for n in numbers if 1 <= int(n) <= len(request.options)]
            elif line.startswith("Explanation:"):
                explanation = line.replace("Explanation:", "").strip()

        if not answer_indices:
            numbers = re.findall(r'\b\d+\b', response_text)
            answer_indices = [int(n) for n in numbers if 1 <= int(n) <= len(request.options)]
            if not answer_indices:
                answer_indices = [1]

        answer_indices = sorted(list(set(answer_indices)))
        if not explanation:
            explanation = response_text

        return QuizResponse(
            question=request.question,
            options=request.options,
            answer_indices=answer_indices,
            explanation=explanation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
