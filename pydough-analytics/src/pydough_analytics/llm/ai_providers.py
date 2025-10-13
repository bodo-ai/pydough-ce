import os
import json
import boto3
from abc import ABC, abstractmethod
from botocore.config import Config
import google.genai as genai
from google.genai import types
from anthropic import AnthropicVertex
import aisuite as ai


class AIProvider(ABC):
    @abstractmethod
    def ask(self, question, prompt, **kwargs):
        pass


class ClaudeAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        self.project = os.environ["GOOGLE_PROJECT_ID"]
        self.location = "us-east5"
        self.model_id = model_id
        self.client = AnthropicVertex(project_id=self.project, region=self.location)

    def ask(self, question, prompt, **kwargs):
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


class GeminiAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        self.project = os.environ["GOOGLE_PROJECT_ID"]
        self.location = os.environ["GOOGLE_REGION"]
        self.model_id = model_id
        self.client = genai.Client(project=self.project, location=self.location)

    def ask(self, question, prompt, **kwargs):
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                **kwargs
            ),
        )
        return response.text, response.usage_metadata


class OtherAIProvider(AIProvider):
    def __init__(self, provider, model_id, config=None):
        self.client = ai.Client(config) if config else ai.Client()
        self.provider = provider
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        response = self.client.chat.completions.create(
            model=f"{self.provider}:{self.model_id}",
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


def get_provider(provider, model_id, config=None):
    if provider == "anthropic":
        return ClaudeAIProvider(model_id, config=config)
    elif provider == "google":
        return GeminiAIProvider(model_id, config=config)
    else:
        return OtherAIProvider(provider, model_id, config)
