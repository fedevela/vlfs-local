import json
import subprocess
from google import genai

class LLMAdapter:
    """A simple adapter to toggle between the google-genai SDK and the local dev tools."""
    
    def __init__(self, local_dev_mode: bool = False):
        self.local_dev_mode = local_dev_mode
        if not self.local_dev_mode:
            self.client = genai.Client()

    def generate_summary(self, model: str, prompt: str) -> str:
        if self.local_dev_mode:
            # We call the gemini-cli headless, letting it choose the default model
            cmd = ["gemini", "-p", prompt, "-o", "json"]
            try:
                # Capture stdout independently to avoid pollution from stderr logs
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                # Find the first '{' to parse the json, since there might be preamble logs
                stdout = result.stdout
                json_start = stdout.find('{')
                if json_start != -1:
                    data = json.loads(stdout[json_start:])
                    return data.get("response", "Summary unavailable.").strip()
                return "Summary unavailable."
            except Exception as e:
                print(f"gemini-cli generation failed: {e}")
                return "Summary unavailable."
        else:
            response = self.client.models.generate_content(model=model, contents=prompt)
            return response.text.strip() if response.text else "Summary unavailable."

    def embed_content(self, model: str, contents: list[str]) -> list[list[float]]:
        """Returns a unified list of float arrays."""
        if self.local_dev_mode:
            import ollama
            response = ollama.embed(model='nomic-embed-text', input=contents)
            return response['embeddings']
        else:
            response = self.client.models.embed_content(model=model, contents=contents)
            return [emb.values for emb in response.embeddings]
