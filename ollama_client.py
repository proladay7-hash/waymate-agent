import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import urllib.request
import urllib.error

# Try importing requests, fallback to urllib if not installed
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model_name: str = "qwen2.5:0.5b"):
        self.model_name = os.getenv("OLLAMA_MODEL", model_name)
        self.base_url = os.getenv("OLLAMA_HOST", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        self._response_cache = {}
        
    def _is_server_listening(self, timeout: float = 0.5) -> bool:
        """Fast TCP check to determine if Ollama port is open without blocking"""
        import socket
        from urllib.parse import urlparse
        try:
            parsed = urlparse(self.base_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 11434
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    async def check_health(self) -> bool:
        """Check if Ollama is running and model is available"""
        if not await asyncio.to_thread(self._is_server_listening):
            return False

        try:
            url = f"{self.base_url}/api/tags"
            if HAS_REQUESTS:
                response = await asyncio.to_thread(requests.get, url, timeout=1.5)
                if response.status_code != 200:
                    return False
                data = response.json()
            else:
                def _urllib_get():
                    req = urllib.request.Request(url)
                    with urllib.request.urlopen(req, timeout=1.5) as resp:
                        return json.loads(resp.read().decode('utf-8'))
                data = await asyncio.to_thread(_urllib_get)
            
            available_models = [m.get('name', '') for m in data.get('models', [])]
            model_base = self.model_name.split(':')[0]
            is_avail = any(self.model_name in name or model_base in name for name in available_models)
            
            if not is_avail:
                logger.warning(f"Model {self.model_name} not found in available models: {available_models}")
                return False
                
            return True
        except Exception as e:
            logger.debug(f"Health check error: {e}")
            return False
    
    async def generate_response(
        self, 
        message: str, 
        context: str = "", 
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using Ollama llama3.2:1b or return unavailable message on failure"""
        try:
            cache_key = message.lower().strip()
            if cache_key in self._response_cache:
                logger.info("Using cached response")
                return self._response_cache[cache_key]
            
            # Verify Ollama and model availability
            is_healthy = await self.check_health()
            if not is_healthy:
                logger.error(f"Ollama or model {self.model_name} is not available.")
                return self._get_unavailable_message(message)
            
            system_prompt = self._create_system_prompt(context)
            messages = self._prepare_messages(system_prompt, message, history or [])
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 300
                }
            }
            
            chat_url = f"{self.base_url}/api/chat"
            timeout_sec = int(os.getenv("OLLAMA_TIMEOUT", "60"))
            
            if HAS_REQUESTS:
                response = await asyncio.to_thread(
                    requests.post,
                    chat_url,
                    json=payload,
                    timeout=timeout_sec
                )
                if response.status_code == 200:
                    res_data = response.json()
                    response_text = res_data.get('message', {}).get('content', '').strip()
                    if response_text:
                        self._response_cache[cache_key] = response_text
                        return response_text
            else:
                def _urllib_post():
                    req = urllib.request.Request(
                        chat_url,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                        return json.loads(resp.read().decode('utf-8'))
                res_data = await asyncio.to_thread(_urllib_post)
                response_text = res_data.get('message', {}).get('content', '').strip()
                if response_text:
                    self._response_cache[cache_key] = response_text
                    return response_text

            logger.warning("Empty response received from Ollama model.")
            return self._get_unavailable_message(message)

        except Exception as e:
            logger.error(f"Error calling Ollama model: {e}")
            return self._get_unavailable_message(message)

    def _is_vietnamese(self, text: str) -> bool:
        """Detect if message is likely Vietnamese"""
        vn_chars = ['à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ', 'â', 'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ',
                    'è', 'é', 'ẻ', 'ẽ', 'ẹ', 'ê', 'ề', 'ế', 'ể', 'ễ', 'ệ',
                    'ì', 'í', 'ỉ', 'ĩ', 'ị',
                    'ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ồ', 'ố', 'ổ', 'ỗ', 'ộ', 'ơ', 'ờ', 'ớ', 'ở', 'ỡ', 'ợ',
                    'ù', 'ú', 'ủ', 'ũ', 'ụ', 'ư', 'ừ', 'ứ', 'ử', 'ữ', 'ự',
                    'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ', 'đ']
        vn_words = ['chuyến', 'phượt', 'nhớt', 'xe', 'đèo', 'bảo dưỡng', 'bản đồ', 'chào', 'bạn', 'mật khẩu', 'hà giang', 'đà lạt']
        text_lower = text.lower()
        if any(c in text_lower for c in vn_chars):
            return True
        if any(w in text_lower for w in vn_words):
            return True
        return False

    def _get_unavailable_message(self, message: str) -> str:
        """Display unavailable message when model fails or Ollama is offline"""
        if self._is_vietnamese(message):
            return (
                f"Trợ lý WayMate AI hiện không khả dụng. "
                f"Vui lòng đảm bảo dịch vụ Ollama đang hoạt động với mô hình {self.model_name}."
            )
        else:
            return (
                f"WayMate AI Agent is currently not available. "
                f"Please ensure Ollama is running with model {self.model_name}."
            )

    def _create_system_prompt(self, context: str) -> str:
        """Create system prompt tailored for WayMate AI Agent"""
        base_prompt = """You are WayMate AI Agent (Trợ lý WayMate AI) — the dedicated self-built AI assistant for the WayMate app, an adventure travel, motorcycle, and road trip platform.

Your knowledge and core responsibilities:
1. Adventure Trips & Routes: Ha Giang Extreme Northern Loop (350 km), Saigon to Da Lat (310 km), Pacific Coast Highway 1 (720 km), route elevations, pit stops, lodging, and telemetry (avg speed, max velocity, distance).
2. Vehicle Garage & Maintenance Tracking: Recommended engine oil replacement intervals (3,000 km for motorcycles, 5,000 km for cars), ODO calculations, oil status (Good vs Due Soon), logging oil changes, and service history (Brembo pads, Motul 300V oil, tire replacements, valve checks).
3. Navigation: Google Maps route preview, pinning GPS coordinates (latitude/longitude), custom shortened map links, GPX route exports.
4. Profile & Badges: Verified Rider, PRO, Iron Butt 1000km, Ha Giang Master, Highland Explorer, Coast Rider, Trailblazer.
5. Account & Security: Google 1-Tap sign-in, 3-step OTP password recovery (Email -> 6-digit OTP -> Set new password).
6. App Settings: Dark/Light theme modes, English/Vietnamese language toggle, KM/Miles units.

Tone & Guidelines:
- Helpful, professional, accurate, and concise.
- Automatically respond in the user's language (English or Vietnamese).
- Format responses cleanly with bullet points and emojis. Keep responses under 250 words unless detailed information is requested."""

        if context:
            base_prompt += f"\n\nWayMate Knowledge Base Context:\n{context}"

        return base_prompt

    def _prepare_messages(
        self, 
        system_prompt: str, 
        user_message: str, 
        history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Prepare messages for Ollama API"""
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-8:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        messages.append({
            "role": "user",
            "content": user_message
        })
        return messages
