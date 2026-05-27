from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from week_2.prompt_model import OllamaClient

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use host.docker.internal when running in Docker, localhost otherwise
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/generate"

client = OllamaClient(base_url=OLLAMA_URL)


class ChatRequest(BaseModel):
    message: str
    pdf_text: str | None = None


@app.post("/chat")
async def chat(body: ChatRequest):
    try:
        prompt = body.message
        if body.pdf_text:
            prompt = (
                f"The user has provided the following document:\n\n"
                f"{body.pdf_text}\n\n"
                f"User message: {body.message}"
            )

        response, tokens, elapsed = client.generate(prompt)

        return JSONResponse(content={"response": response})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))