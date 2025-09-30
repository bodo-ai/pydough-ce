import os
import json
import boto3
from abc import ABC, abstractmethod
from botocore.config import Config
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
import google.genai as genai
from google.genai import types
from mistralai import Mistral
from anthropic import AnthropicVertex
import aisuite as ai


class AIProvider(ABC):
    @abstractmethod
    def ask(self, question, prompt, **kwargs):
        pass


class AzureAIProvider(AIProvider):
    def __init__(self, model_id):
        self.client = self.setup_azure_client()
        self.model_id = model_id

    def setup_azure_client(self):
        endpoint = os.getenv("AZURE_BASE_URL")
        key = os.getenv("AZURE_API_KEY")
        if not endpoint or not key:
            raise ValueError("Azure environment variables are not set.")
        return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def ask(self, question, prompt, **kwargs):
        messages = [SystemMessage(prompt), UserMessage(question)]
        completion = self.client.complete(messages=messages, max_tokens=kwargs.get("max_tokens", 20000),
                                          model=self.model_id, stream=True)
        return "".join([chunk.choices[0]["delta"]["content"] for chunk in completion if chunk.choices])


class ClaudeAIProvider(AIProvider):
    def __init__(self, model_id, config=None):
        self.api_key = os.environ["GOOGLE_API_KEY"]
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
        self.api_key = os.environ["GOOGLE_API_KEY"]
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


class DeepSeekAIProvider(AIProvider):
    def __init__(self, model_id):
        config = Config(read_timeout=500)
        self.brt = boto3.client(service_name='bedrock-runtime', config=config)
        self.model_id = model_id

    def ask(self, question, prompt, **kwargs):
        system_messages = [{"text": prompt}]
        messages = [{"role": "user", "content": [{"text": question}]}]
        response = self.brt.converse(
            modelId=self.model_id,
            inferenceConfig={"maxTokens": kwargs.get("max_tokens", 30000), **kwargs},
            system=system_messages,
            messages=messages
        )
        return response["output"]["message"]["content"][0]["text"]


class MistralAIProvider(AIProvider):
    def __init__(self, model_id):
        self.api_key = os.environ["MISTRAL_API_KEY"]
        self.model_id = model_id
        self.client = Mistral(api_key=self.api_key)

    def ask(self, question, prompt, **kwargs):
        messages = [{"role": "system", "content": prompt}, {"role": "user", "content": question}]
        response = self.client.chat.complete(
            model=self.model_id,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


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
    elif provider == "azure":
        return AzureAIProvider(model_id)
    elif provider == "aws-deepseek":
        return DeepSeekAIProvider(model_id)
    elif provider == "google":
        return GeminiAIProvider(model_id, config=config)
    elif provider == "mistral":
        return MistralAIProvider(model_id)
    else:
        return OtherAIProvider(provider, model_id, config)
