import time
import re
import requests
from typing import Optional, Tuple

# ----------------- Configuration -----------------
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1"          # Change to deepseek-r1:1.5b or llama3.1 if desired
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 200
RETRY_DELAY = 2
MAX_RETRIES = 3
# -------------------------------------------------


class OllamaClient:
    """Simple client to interact with a local Ollama instance."""

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str,
                 temperature: float = DEFAULT_TEMPERATURE,
                 max_tokens: int = DEFAULT_MAX_TOKENS,
                 timeout: int = 30) -> Tuple[str, int, float]:
        """
        Send a prompt to Ollama and return (response_text, estimated_tokens, elapsed_ms).
        """
        start_time = time.time()

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data.get("response", "").strip()

                    # Rough token estimation (4 chars per token)
                    estimated_tokens = (len(prompt) + len(answer)) // 4
                    elapsed_ms = (time.time() - start_time) * 1000
                    return answer, estimated_tokens, elapsed_ms
                else:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return f"HTTP {resp.status_code}: {resp.text[:100]}", 0, 0
            except requests.exceptions.ConnectionError:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return "Error: Ollama not running. Start with 'ollama serve'", 0, 0
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return f"Unexpected error: {e}", 0, 0

        return "Max retries exceeded", 0, 0


# -------------------------------------------------
# Example usage (if run as a script)
if __name__ == "__main__":
    import sys

    client = OllamaClient()

    # Simple interactive loop
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        response, tokens, elapsed = client.generate(prompt)
        print(f"Response: {response}")
        print(f"Estimated tokens: {tokens}, time: {elapsed:.2f}ms")
    else:
        print("Ollama Prompt Model – Interactive Mode (type 'exit' to quit)")
        while True:
            user_input = input("\nPrompt: ")
            if user_input.lower() in ("exit", "quit"):
                break
            response, tokens, elapsed = client.generate(user_input)
            print(f"Response: {response}")
            print(f"Tokens (est): {tokens}, time: {elapsed:.2f}ms")