import json
import subprocess
import os
from .config import load_config

class LLMAdapter:
    """A simple adapter to toggle between different LLM and embedding providers based on config."""
    
    def __init__(self, local_dev_mode: bool = False):
        self.local_dev_mode = local_dev_mode
        self.config = load_config()
        self.vlm_provider = self.config.get("vlm", {}).get("provider", "google")
        self.embedding_provider = self.config.get("embedding", {}).get("provider", "google")
        
        self.google_client = None
        self.openai_client = None

        if not self.local_dev_mode:
            if self.vlm_provider == "google" or self.embedding_provider == "google":
                from google import genai
                self.google_client = genai.Client(api_key=self.config.get("vlm", {}).get("api_key", os.environ.get("GEMINI_API_KEY")))
            
            if self.vlm_provider == "openai" or self.embedding_provider == "openai":
                try:
                    import openai
                    self.openai_client = openai.OpenAI(api_key=self.config.get("vlm", {}).get("api_key", os.environ.get("OPENAI_API_KEY")))
                except ImportError:
                    print("Warning: openai package not installed. OpenAI provider will fail.")

    def generate_summary(self, model: str, prompt: str) -> str:
        if self.local_dev_mode:
            # We call the gemini-cli headless, letting it choose the default model
            cmd = ["gemini", "-p", prompt, "-o", "json"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
            if self.vlm_provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=model or self.config["vlm"]["model"],
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()
            elif self.google_client:
                response = self.google_client.models.generate_content(
                    model=model or self.config["vlm"]["model"],
                    contents=prompt
                )
                return response.text.strip() if response.text else "Summary unavailable."
            else:
                return "Summary unavailable. Provider not configured properly."

    def embed_content(self, model: str, contents: list[str]) -> list[list[float]]:
        """Returns a unified list of float arrays."""
        if self.local_dev_mode:
            import ollama
            response = ollama.embed(model='nomic-embed-text', input=contents)
            return response['embeddings']
        else:
            if self.embedding_provider == "openai" and self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=model or self.config["embedding"]["model"],
                    input=contents
                )
                return [data.embedding for data in response.data]
            elif self.google_client:
                response = self.google_client.models.embed_content(
                    model=model or self.config["embedding"]["model"],
                    contents=contents
                )
                return [emb.values for emb in response.embeddings]
            else:
                raise Exception("Embedding provider not configured properly.")
