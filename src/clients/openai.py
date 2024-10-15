from typing import List, Any
import openai
from .base import BaseAIClient
from src.core.config import Config
from src.utils.monitor import Monitor

class OpenAIClient(BaseAIClient):
    def __init__(self):
        self.config = Config()
        self.monitor = Monitor(__name__)
        openai.api_key = self.config.openai.api_key
        self.monitor.log_info("OpenAIClient initialized")

    async def generate_response(self, prompt: str) -> str:
        try:
            response = await openai.ChatCompletion.create(
                model=self.config.openai.model,
                messages=[{"role": "user", "content": prompt}]
            )
            self.monitor.log_info("Generated response successfully")
            return response['choices'][0]['message']['content']
        except Exception as e:
            self.monitor.log_error(e)
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            response = await openai.Embedding.create(
                model=self.config.openai.embedding_model,
                input=texts
            )
            self.monitor.log_info(f"Embedded {len(texts)} texts successfully")
            return [embedding['embedding'] for embedding in response['data']]
        except Exception as e:
            self.monitor.log_error(e)
            raise

    async def generate_image(self, prompt: str) -> str:
        try:
            response = await openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            self.monitor.log_info("Generated image successfully")
            return response['data'][0]['url']
        except Exception as e:
            self.monitor.log_error(e)
            raise

    async def analyze_image(self, image_url: str) -> Any:
        try:
            response = await openai.Image.create(
                url=image_url,
                model="vision-model"
            )
            self.monitor.log_info("Analyzed image successfully")
            return response['data']
        except Exception as e:
            self.monitor.log_error(e)
            raise

# Example usage
# openai_client = OpenAIClient(api_key='your_api_key')
# response = await openai_client.generate_response("What is AI?")
# embeddings = await openai_client.embed_texts(["Hello", "World"])
# image_url = await openai_client.generate_image("A beautiful sunset")
# analysis = await openai_client.analyze_image(image_url)
