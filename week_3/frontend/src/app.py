from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat_page.html",
        context={"backend_url": BACKEND_URL},
    )