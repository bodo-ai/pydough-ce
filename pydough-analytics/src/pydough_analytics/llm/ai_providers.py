import os
from abc import ABC, abstractmethod
import google.genai as genai
from google.genai import types
from anthropic import AnthropicVertex
import aisuite as ai
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class AIProvider(ABC):
    @abstractmethod
    def ask(self, question, prompt, **kwargs):
        pass


class ClaudeAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        try:
            self.project = os.getenv("GOOGLE_PROJECT_ID")
            self.location = os.getenv("GOOGLE_REGION", "us-east5")
            self.model_id = model_id

            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not self.project or not creds_path:
                raise ValueError("Missing GOOGLE_PROJECT_ID or GOOGLE_APPLICATION_CREDENTIALS.")

            self.client = AnthropicVertex(project_id=self.project, region=self.location)
        except Exception as e:
            raise ValueError(f"Error initializing ClaudeAIProvider: {e}")

    def ask(self, question, prompt, **kwargs):
        try:
            kwargs.setdefault("max_tokens", 20000)
            response_stream = self.client.messages.create(
                messages=[{"role": "user", "content": question}],
                model=self.model_id,
                system=prompt,
                stream=True,
                **kwargs
            )
            full_output = ""
            for chunk in response_stream:
                data = chunk.to_dict() if hasattr(chunk, "to_dict") else chunk
                if data.get("type") == "content_block_delta":
                    delta = data.get("delta", {})
                    if delta.get("type") == "text_delta":
                        full_output += delta.get("text", "")
            return full_output, None
        except Exception as e:
            raise ValueError(f"Error during ask in ClaudeAIProvider: {e}")


class GeminiAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        try:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            self.project = os.getenv("GOOGLE_PROJECT_ID")
            self.location = os.getenv("GOOGLE_REGION", "us-central1")
            self.use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() in ("1", "true", "yes")
            self.model_id = model_id
            if self.use_vertex:
                if not self.project:
                    raise ValueError("Missing GOOGLE_PROJECT_ID for Vertex mode.")
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=self.location
                )
            else:
                if not self.api_key:
                    raise ValueError("Missing GOOGLE_API_KEY for non-Vertex mode")
                self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Error initializing GeminiAIProvider: {e}")

    def ask(self, question, prompt, **kwargs):
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    **kwargs
                ),
            )
            return response.text, response.usage_metadata
        except Exception as e:
            raise ValueError(f"Error during ask in GeminiAIProvider: {e}")


class OllamaAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        self.model_id = model_id
        self.base_url = os.getenv("OLLAMA_BASE_URL")

    def ask(self, question, prompt, **kwargs):
        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_ctx": 8192,
            },
        }

        r = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=600,
        )
        r.raise_for_status()

        return r.json()["message"]["content"]


class OtherAIProvider(AIProvider):
    def __init__(self, provider, model_id, config=None):
        try:
            self.client = ai.Client(config) if config else ai.Client()
            self.provider = provider
            self.model_id = model_id
        except Exception as e:
            raise ValueError(f"Error initializing other provider: {e}")

    def ask(self, question, prompt, **kwargs):
        try:
            messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
            response = self.client.chat.completions.create(
                model=f"{self.provider}:{self.model_id}",
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Error during ask in other provider: {e}")


def get_provider(provider, model_id, config=None):
    try:
        if provider == "anthropic":
            return ClaudeAIProvider(model_id, config=config)
        elif provider == "google":
            return GeminiAIProvider(model_id, config=config)
        elif provider == "ollama":
            return OllamaAIProvider(model_id, config=config)
        else:
            return OtherAIProvider(provider, model_id, config)
    except Exception as e:
        raise ValueError(f"Error getting provider {provider}: {e}")
