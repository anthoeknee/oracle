# clients/base.py
from abc import ABC, abstractmethod

class BaseAIClient(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        pass
