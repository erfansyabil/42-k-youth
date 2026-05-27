# Week 3 – Full-Stack Containerized Chat Application

A full-stack chat application with a FastAPI frontend, FastAPI backend, and local LLM integration via Ollama. Both services are containerized with Docker and orchestrated with Docker Compose.

---

## Project Overview

This project builds a resume helper chatbot. Users can type messages and optionally upload a PDF (e.g. a resume), which is extracted in the browser and sent to the backend. The backend forwards the prompt to a local Ollama LLM and returns the response to the frontend.

The system is split into two independent services:

- **Frontend** — serves the chat UI and handles PDF extraction in the browser
- **Backend** — exposes a REST API that calls the Ollama LLM and returns a response

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/) installed and running locally
- The model you want to use pulled locally, e.g.:
  ```bash
  ollama pull phi3:latest
  ```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd week_3
```

### 2. Configure environment variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
BACKEND_URL=http://localhost:8001
OLLAMA_HOST=http://host.docker.internal:11434
```

> `BACKEND_URL` is used by the browser to reach the backend.  
> `OLLAMA_HOST` is used by the backend container to reach Ollama running on your machine.

### 3. Start Ollama

In a separate terminal, make sure Ollama is running:

```bash
ollama serve
```

---

## Usage

### Run with Docker Compose (recommended)

From the `week_3/` directory:

```bash
docker compose up --build
```

- Frontend: [http://localhost:8000](http://localhost:8000)
- Backend API docs: [http://localhost:8001/docs](http://localhost:8001/docs)

### Run manually (without Docker)

**Frontend:**
```bash
cd frontend
uv sync
uv run uvicorn --app-dir src app:app --reload
```

**Backend:**
```bash
cd backend
uv sync
uv run uvicorn --app-dir src app:app --reload --port 8001
```

### Using the chat interface

1. Open [http://localhost:8000](http://localhost:8000) in your browser
2. Type a message in the input box and press Enter or click Send
3. Optionally click the attachment icon to upload a PDF — the text will be extracted in the browser and included with your message
4. The chatbot will respond using the configured Ollama model

---

## API / Function Reference

### Backend — `POST /chat`

Endpoint for sending a message to the LLM.

**Request body (JSON):**
```json
{
  "message": "Can you improve my resume summary?",
  "pdf_text": "John Smith\nSoftware Engineer..."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | The user's chat message |
| `pdf_text` | string | No | Extracted text from an uploaded PDF |

**Response (JSON):**
```json
{
  "response": "Here are some suggestions for improving your summary..."
}
```

**Error response:**
```json
{
  "detail": "Error message here"
}
```

### Frontend — Key JavaScript functions

| Function | Description |
|---|---|
| `sendMessage()` | Reads user input, optionally attaches PDF text, sends `POST /chat` to the backend, and renders the response |
| `handleFileSelect(event)` | Reads the uploaded PDF using pdf.js and stores the extracted text in memory |
| `extractPdfText(file)` | Uses pdf.js to extract all text from a PDF file page by page |
| `appendMessage(role, text)` | Renders a new chat bubble in the chat history |
| `clearFile()` | Removes the attached PDF from the pending state |

### Service communication

When running via Docker Compose, both services share the `app-network` bridge network. The browser always communicates with the backend via `http://localhost:8001` (configured in `BACKEND_URL`). Container-to-container communication is not used for chat requests since the JavaScript runs in the browser.

---

## Data / Assumptions

### Message flow

1. User types a message (and optionally uploads a PDF) in the browser
2. If a PDF is attached, `pdf.js` extracts the text entirely in the browser — no file is uploaded to the server
3. The browser sends a `POST /chat` JSON request to the backend at `BACKEND_URL`
4. The backend builds a prompt (prepending the PDF text if present) and calls the Ollama API
5. Ollama returns a generated response, which the backend forwards as JSON to the frontend
6. The frontend renders the response as a chat bubble

### Assumptions and constraints

- PDF text extraction is limited to text-based PDFs. Scanned image PDFs will produce empty or garbled text.
- PDF content is truncated to the first 2000 characters before being sent to the model to avoid exceeding context limits.
- The Ollama model must be running on the host machine before starting the containers.
- Chat history is stored only in the browser — refreshing the page clears it.
- No user authentication is implemented.
- The backend does not maintain conversation history between requests; each message is a standalone prompt.

---

## Testing

### Backend — test with curl (PowerShell)

```powershell
Invoke-WebRequest -Uri http://localhost:8001/chat `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"message": "What skills should a software engineer have?"}'
```

### Backend — test with curl (bash/terminal)

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What skills should a software engineer have?"}'
```

### Backend — interactive test UI

Visit [http://localhost:8001/docs](http://localhost:8001/docs) — FastAPI's built-in Swagger UI lets you send test requests directly from the browser.

### Frontend test cases

| Test | Steps | Expected result |
|---|---|---|
| Send a message | Type text, press Enter | Response bubble appears |
| Upload a PDF | Click attachment icon, select a PDF, send a message | File badge shown, PDF text included in prompt |
| Remove attachment | Click ✕ on the file strip | File cleared, next message sent without PDF |
| Backend unreachable | Stop the backend container, send a message | Error toast shown, warning bubble rendered |

### Verifying Docker networking

```bash
# Confirm both containers are on the same network
docker network inspect week_3_app-network

# Check backend logs inside compose
docker compose logs backend
```

---

## Limitations

- **No conversation memory** — the model receives only the current message; it has no context from previous turns.
- **No persistent storage** — chat history is lost on page refresh. There is no database.
- **PDF quality** — scanned or image-based PDFs will not extract meaningful text.
- **Model accuracy** — responses depend entirely on the local Ollama model quality. Smaller models (e.g. `phi3:latest`) may produce inconsistent or incorrect answers.
- **No authentication** — anyone with access to the URL can use the chat interface.
- **Single user** — there is no session management; multiple simultaneous users would share the same stateless backend.
- **Ollama must run on host** — the backend container connects to Ollama via `host.docker.internal`. Ollama is not containerized in the mandatory section.

---

## Architecture Reflection

### Design choices

The project uses a microservices architecture with a separate frontend and backend container. This separation means each service can be developed, rebuilt, and scaled independently. Docker ensures the application runs identically regardless of the host machine.

The frontend is a FastAPI server that serves a single HTML page — using Jinja2 to inject the backend URL at render time so it never needs to be hardcoded. PDF extraction happens entirely in the browser using `pdf.js`, which avoids the complexity of file uploads and reduces backend load.

The backend is a thin API layer — it receives a prompt, calls Ollama, and returns the result. Keeping the LLM logic in the Week 2 `OllamaClient` class means the backend stays simple and the AI integration is reusable.

### Trade-offs

Simplicity was prioritized over features. Using Docker Compose with a bridge network keeps the setup portable and easy to run locally with a single command. The trade-off is that this setup is not production-ready — there is no HTTPS, no auth, and no scalability beyond a single machine.

Stateless request handling (no conversation history) was chosen to keep the backend simple, at the cost of the model not being able to reference earlier messages in a conversation.

### Improvements

Given more time, the following would improve the project significantly:

- **Conversation history** — maintain a message history per session and pass it to the model on each request
- **Database** — store chat sessions with a database like SQLite or PostgreSQL
- **Streaming responses** — stream the LLM output token by token for a more responsive feel
- **Containerized Ollama** — run Ollama as a third Docker service so the entire stack is self-contained and deployable to the cloud
- **Frontend framework** — replace the vanilla JS with React for better state management as the UI grows
- **Authentication** — add user login to support multiple users with separate chat histories
