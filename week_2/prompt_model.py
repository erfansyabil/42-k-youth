import os
import sys
from google import genai

def prompt_model(model: str, prompt: str) -> str:
    """
    Prompts the specified model and returns a text response.
    Smartly handles model selection and errors.
    """
    try:
        # Get API key from environment variable
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "[Error] GOOGLE_API_KEY environment variable not set."

        # Initialize the client
        client = genai.Client(api_key=api_key)

        # Map model shorthand names to full model IDs if needed
        model_mapping = {
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
            "gemini-3-flash-preview": "gemini-3-flash-preview",
        }

        # Resolve the model name
        if model in model_mapping:
            model_id = model_mapping[model]
        else:
            model_id = model  # Pass through as-is for bonus models

        # Generate content
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )

        return response.text

    except Exception as e:
        # Smart error handling — return formatted error instead of crashing
        return f"[Gemini Error] {e}"


def main():
    """
    Main function to test prompt_model.
    Reads model and prompt from command-line arguments.
    """
    if len(sys.argv) < 3:
        print("Usage: uv run prompt_model.py <model> <prompt>")
        print("Example: uv run prompt_model.py gemini-2.5-flash \"tell me a joke\"")
        sys.exit(1)

    model = sys.argv[1]
    prompt = sys.argv[2]

    response = prompt_model(model, prompt)
    print("\n--- RESPONSE ---\n")
    print(response)


if __name__ == "__main__":
    main()