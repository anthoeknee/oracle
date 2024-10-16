import cohere
from src.clients.base import BaseAIClient
from src.core.config import config
from src.utils.monitor import Monitor
import json
from typing import Any, List, Dict

class CohereAIClient(BaseAIClient):
    def __init__(self):
        self.monitor = Monitor(__name__)
        self.client = cohere.Client(config.cohere.api_key)

    def format_tools_for_cohere(self, tools):
        formatted_tools = []
        for tool in tools:
            function = tool.get('function', {})
            if 'name' not in function:
                self.monitor.log_warning(f"Skipping tool without name: {tool}")
                continue
            
            formatted_tool = {
                'name': function['name'],
                'description': function.get('description', ''),
                'parameters': function.get('parameters', {})
            }
            
            if 'required' in tool:
                formatted_tool['parameters']['required'] = tool['required']
            
            formatted_tools.append(formatted_tool)
        
        return formatted_tools

    async def generate_response(self, prompt: str) -> str:
        try:
            response = self.client.generate(
                model=config.cohere.model,
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            self.monitor.log_info("Generated response successfully")
            return response.generations[0].text
        except Exception as e:
            self.monitor.log_error(f"Error generating response: {e}")
            raise

    async def chat(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            chat_history = []
            system_message = None
            for msg in messages:
                role = msg["role"]
                if role == "System":
                    system_message = msg["message"]
                elif role in ["User", "Chatbot"]:
                    chat_history.append({"role": role.lower(), "message": msg["message"]})
            
            user_message = messages[-1]["message"]

            response = self.client.chat(
                model=model,
                message=user_message,
                chat_history=chat_history,
                preamble=system_message,
                temperature=0.7,
                max_tokens=150
            )
            self.monitor.log_info("Chat response generated successfully")
            self.monitor.log_info(f"Raw response: {json.dumps(response.dict(), indent=2)}")

            processed_response = {
                "content": response.text
            }

            self.monitor.log_info(f"Processed response: {json.dumps(processed_response, indent=2)}")
            return processed_response
        except Exception as e:
            self.monitor.log_error(f"Error in chat method: {str(e)}")
            self.monitor.log_error(f"Error details: {type(e).__name__}: {str(e)}")
            raise
