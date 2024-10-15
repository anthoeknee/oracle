from typing import List, Any
import cohere
from .base import BaseAIClient
from src.core.config import Config
from src.utils.monitor import Monitor

class CohereAIClient(BaseAIClient):
    def __init__(self):
        self.config = Config()
        self.monitor = Monitor(__name__)
        self.client = cohere.Client(self.config.cohere.api_key)
        self.monitor.log_info("CohereAIClient initialized")

    async def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.chat(
                message=prompt,
                model=self.config.cohere.model,
                temperature=0.7,
                max_tokens=150
            )
            self.monitor.log_info("Generated response successfully")
            return response.text
        except Exception as e:
            self.monitor.log_error(e)
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            response = await self.client.embed(
                texts=texts,
                model=self.config.cohere.embedding_model
            )
            self.monitor.log_info(f"Embedded {len(texts)} texts successfully")
            return response.embeddings
        except Exception as e:
            self.monitor.log_error(e)
            raise

    async def rerank_responses(self, query: str, responses: List[str]) -> List[Any]:
        try:
            response = await self.client.rerank(
                query=query,
                documents=responses,
                model=self.config.cohere.rerank_model
            )
            self.monitor.log_info(f"Reranked {len(responses)} responses successfully")
            return response.results
        except Exception as e:
            self.monitor.log_error(e)
            raise

# Example usage
# cohere_client = CohereAIClient(api_key='your_api_key')
# response = await cohere_client.generate_response("Hello, how can I help you?")
# embeddings = await cohere_client.embed_texts(["Hello", "World"])
# ranked = await cohere_client.rerank_responses("What is AI?", ["AI is awesome", "AI is a tool"])
