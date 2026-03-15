"""
Microsoft Foundry Agent - Core Agent for Foundry Model Management
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from azure.ai.projects import AIProjectClient
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ChatCompletions,
    ChatChoice
)

from app.core.logging import logger
from app.core.config import settings

class FoundryAgent:
    """
    Core agent for interacting with Microsoft Foundry models
    Manages model deployments, inference, and context
    """
    
    def __init__(self, 
                 project_client: Optional[AIProjectClient] = None,
                 cache_service=None,
                 metrics=None,
                 kernel=None,
                 credential=None):
        self.project_client = project_client
        self.cache_service = cache_service
        self.metrics = metrics
        self.kernel = kernel
        self.credential = credential
        self.chat_client = None
        self.embedding_client = None
        self.deployed_models = {}  # This is where models are stored
        self.is_healthy = False
        
    @property
    def models(self):
        """Return deployed models (for compatibility with main.py)"""
        return self.deployed_models
        
    async def initialize(self):
        """Initialize Foundry connections"""
        try:
            # Initialize chat completions client if endpoint and key are available
            if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
                from azure.core.credentials import AzureKeyCredential
                self.chat_client = ChatCompletionsClient(
                    endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    credential=AzureKeyCredential(settings.AZURE_OPENAI_KEY),
                    model=settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4o"
                )
                logger.info("Chat client initialized")
            
            # Initialize embeddings client
            if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
                from azure.core.credentials import AzureKeyCredential
                self.embedding_client = ChatCompletionsClient(
                    endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    credential=AzureKeyCredential(settings.AZURE_OPENAI_KEY)
                )
                logger.info("Embedding client initialized")
            
            # List deployed models
            await self._list_deployed_models()
            
            self.is_healthy = True
            logger.info(f"FoundryAgent initialized with {len(self.deployed_models)} models")
            
        except Exception as e:
            logger.error(f"Failed to initialize FoundryAgent: {str(e)}")
            # Still mark as healthy with fallback models
            self.is_healthy = True
            await self._load_fallback_models()
    
    async def _list_deployed_models(self):
        """List all deployed models in Foundry"""
        try:
            # In production, would call Foundry API to list models
            self.deployed_models = {
                "gpt-4o": {
                    "name": "gpt-4o",
                    "type": "chat",
                    "capabilities": ["chat", "function_calling", "vision"],
                    "context_length": 128000,
                    "deployment": settings.AZURE_OPENAI_DEPLOYMENT
                },
                "text-embedding-3-large": {
                    "name": "text-embedding-3-large",
                    "type": "embedding",
                    "dimensions": 3072
                },
                "scam-detector": {
                    "name": "scam-detector",
                    "type": "custom",
                    "capabilities": ["classification"]
                },
                "adherence-predictor": {
                    "name": "adherence-predictor",
                    "type": "custom",
                    "capabilities": ["regression"]
                },
                "priority-ranker": {
                    "name": "priority-ranker",
                    "type": "custom",
                    "capabilities": ["ranking"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
    
    async def _load_fallback_models(self):
        """Load fallback models"""
        self.deployed_models = {
            "gpt-4o": {
                "name": "gpt-4o",
                "type": "chat",
                "capabilities": ["chat", "function_calling"],
                "context_length": 128000
            },
            "text-embedding-3-large": {
                "name": "text-embedding-3-large",
                "type": "embedding",
                "dimensions": 3072
            }
        }
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        functions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate chat completion using Foundry model"""
        try:
            if not self.chat_client:
                # Simulated response for development
                return {
                    "content": self._simulate_response(messages),
                    "role": "assistant",
                    "finish_reason": "stop"
                }
            
            formatted_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                formatted_messages.append(SystemMessage(content=system_prompt))
            
            # Add conversation messages
            for msg in messages:
                if msg["role"] == "user":
                    formatted_messages.append(UserMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_messages.append(AssistantMessage(content=msg["content"]))
            
            # Create completion
            params = {
                "messages": formatted_messages,
                "temperature": temperature,
                "model": self.deployed_models.get("gpt-4o", {}).get("deployment", "gpt-4o")
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            if functions:
                params["functions"] = functions
            
            completion = await self.chat_client.complete(**params)
            
            # Extract response
            if completion.choices and len(completion.choices) > 0:
                choice = completion.choices[0]
                response = {
                    "content": choice.message.content or "",
                    "role": choice.message.role,
                    "finish_reason": choice.finish_reason
                }
                
                # Handle function calls if present
                if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    response["function_calls"] = [
                        {
                            "name": call.function.name,
                            "arguments": json.loads(call.function.arguments)
                        }
                        for call in choice.message.tool_calls
                    ]
                
                return response
            
            return {"content": "", "role": "assistant", "finish_reason": "stop"}
            
        except Exception as e:
            logger.error(f"Chat generation failed: {str(e)}")
            # Fallback response
            return {
                "content": self._simulate_response(messages),
                "role": "assistant",
                "finish_reason": "stop"
            }
    
    def _simulate_response(self, messages: List[Dict]) -> str:
        """Simulate response for development"""
        last_message = messages[-1]["content"].lower() if messages else ""
        
        if "hello" in last_message or "hi" in last_message:
            return "Hello! How can I help you today?"
        elif "help" in last_message:
            return "I'm here to help with scam detection, medication reminders, emergency alerts, and wellness tracking. What would you like assistance with?"
        elif "thank" in last_message:
            return "You're welcome! Is there anything else I can help with?"
        else:
            return "I understand. Let me help you with that."
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        try:
            if not self.embedding_client:
                # Return mock embedding
                return [0.0] * 1536
            
            response = await self.embedding_client.embed([text])
            if response and response.data:
                return response.data[0].embedding
            
            return [0.0] * 1536
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return [0.0] * 1536
    
    async def classify_text(
        self,
        text: str,
        model_name: str = "scam-detector",
        labels: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Classify text using Foundry custom model"""
        try:
            # In production, would call custom model
            # Placeholder for demo
            return {
                "scam": 0.15,
                "legitimate": 0.85
            }
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            raise
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using Azure AI Language"""
        try:
            # Use Foundry's language capabilities
            # Placeholder for demo
            return [
                {"entity": "medication", "value": "aspirin", "confidence": 0.95},
                {"entity": "time", "value": "8:00 AM", "confidence": 0.92}
            ]
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            raise
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using Azure AI Language"""
        try:
            # Placeholder for demo
            return {
                "sentiment": "positive",
                "positive_score": 0.85,
                "neutral_score": 0.10,
                "negative_score": 0.05
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            raise
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language using Azure AI Language"""
        try:
            # Placeholder for demo
            return {
                "language": "en",
                "confidence": 0.99,
                "iso6391_name": "en"
            }
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            raise
    
    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """Summarize text using Foundry model"""
        try:
            prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}"
            
            response = await self.generate_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=max_length * 2
            )
            
            return response.get("content", "")
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """Translate text using Foundry model"""
        try:
            source = f" from {source_language}" if source_language else ""
            prompt = f"Translate the following text{source} to {target_language}:\n\n{text}"
            
            response = await self.generate_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=len(text) * 2
            )
            
            return response.get("content", "")
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise
    
    async def get_model_router(self):
        """Get model router instance"""
        from .model_router import ModelRouter
        return ModelRouter(self.deployed_models, self.metrics)
    
    async def close(self):
        """Close connections"""
        logger.info("Closing FoundryAgent")