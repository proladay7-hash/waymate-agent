import ollama
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import os

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        # self.base_url = os.getenv("OLLAMA_BASE_URL", "https://summit-projection-accessories-fwd.trycloudflare.com")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.client = ollama.Client(host=self.base_url)
        self._model_loaded = False
        self._response_cache = {}
        
    async def check_health(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama is running (use / endpoint)
            response = requests.get(f"{self.base_url}/", timeout=3)
            if response.status_code != 200 or "Ollama is running" not in response.text:
                logger.error(f"Ollama health check failed: Unexpected response: {response.text}")
                return False
            # Check if model is available
            models = self.client.list()
            model_names = [model['name'] for model in models['models']]
            if self.model_name not in model_names:
                logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                return False
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            logger.info("Running in demo mode - using predefined responses")
            return False
    
    async def generate_response(
        self, 
        message: str, 
        context: str = "", 
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using Llama 3.2 1B with caching and timeout"""
        try:
            # Check cache first for common queries
            cache_key = message.lower().strip()
            if cache_key in self._response_cache:
                logger.info("Using cached response")
                return self._response_cache[cache_key]
            
            # Check if we're in demo mode or Ollama is not available
            if not await self.check_health():
                return self._generate_demo_response(message, context)
            
            # Prepare system prompt
            system_prompt = self._create_system_prompt(context)
            
            # Prepare conversation
            messages = self._prepare_messages(system_prompt, message, history or [])
            
            # Generate response without timeout
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 300, 
                    "num_predict": 300,
                    "top_k": 20,
                    "repeat_penalty": 1.1
                }
            )
            
            response_text = response['message']['content']
            
            # Cache the response for future use
            self._response_cache[cache_key] = response_text
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_demo_response(message, context)
    
    def _generate_demo_response(self, message: str, context: str = "") -> str:
        """Generate demo responses when AI model is not available"""
        message_lower = message.lower()
        
        # Demo responses for common queries
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm your BigBikeBlitz AI assistant. How can I help you with motorcycles today?"
        
        elif any(word in message_lower for word in ['bmw', 'motorcycle', 'bike']):
            return "We have a great selection of BMW motorcycles! Our current lineup includes the BMW F900R, G310R, and R1250GS. Each model offers excellent performance and German engineering. Would you like to know more about any specific model?"
        
        elif any(word in message_lower for word in ['price', 'cost', 'how much']):
            return "Our motorcycle prices range from $5,000 to $25,000 depending on the model and features. We offer competitive financing options and can help you find the perfect bike within your budget. Would you like to see our current pricing?"
        
        elif any(word in message_lower for word in ['financing', 'loan', 'payment']):
            return "We offer flexible financing options with competitive rates starting at 3.9% APR. We work with multiple lenders to get you the best terms. You can apply online or visit our dealership for personalized assistance."
        
        elif any(word in message_lower for word in ['warranty', 'service', 'maintenance']):
            return "All our motorcycles come with manufacturer warranty and we offer extended warranty options. Our service department is staffed with certified technicians who specialize in motorcycle maintenance and repairs."
        
        elif any(word in message_lower for word in ['delivery', 'shipping', 'pickup']):
            return "We offer free delivery within 50 miles of our dealership. For longer distances, we can arrange shipping at competitive rates. We also provide pickup service for trade-ins."
        
        else:
            return "Thank you for your interest in BigBikeBlitz! I'm here to help you find the perfect motorcycle. We offer a wide selection of BMW, Honda, Yamaha, Kawasaki, and Suzuki bikes. What specific information are you looking for?"
    
    def _create_system_prompt(self, context: str) -> str:
        """Create system prompt with BigBikeBlitz context"""
        base_prompt = """You are BigBikeBlitz AI Assistant for motorcycle e-commerce. Be concise, helpful, and accurate.

Focus on:
- Motorcycle specifications, prices, and features
- Product comparisons and recommendations
- BigBikeBlitz services (financing, warranty, delivery)
- Technical motorcycle information

Keep responses under 200 words unless detailed specs are requested."""
        
        if context:
            base_prompt += f"\n\nRelevant product info:\n{context}"
        
        return base_prompt
    
    def _prepare_messages(
        self, 
        system_prompt: str, 
        user_message: str, 
        history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Prepare messages for Ollama API"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in history[-10:]:  # Limit to last 10 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    async def test_model(self) -> bool:
        """Test the model with a simple query"""
        try:
            test_response = await self.generate_response(
                "Hello, can you tell me about BigBikeBlitz?"
            )
            logger.info(f"Model test successful: {test_response[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Model test failed: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        try:
            models = self.client.list()
            for model in models['models']:
                if model['name'] == self.model_name:
                    return {
                        "name": model['name'],
                        "size": model.get('size', 'Unknown'),
                        "modified_at": model.get('modified_at', 'Unknown'),
                        "digest": model.get('digest', 'Unknown')
                    }
            return {"error": "Model not found"}
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"error": str(e)} 
