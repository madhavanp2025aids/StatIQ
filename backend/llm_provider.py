import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from google import genai
from google.genai import types
from groq import Groq

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_content(self, system_instruction: str, messages: List[Dict[str, str]]) -> str:
        """
        Generates content from the LLM.
        Args:
            system_instruction: The system prompt.
            messages: List of dicts with 'role' (user/model) and 'text' keys.
        Returns:
            The raw text response from the LLM.
        """
        pass

class GeminiProvider(LLMProvider):
    """Google Gemini provider via google-genai SDK."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        self.client = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, system_instruction: str, messages: List[Dict[str, str]]) -> str:
        if not self.client:
            raise ValueError("Gemini API key not configured properly.")
            
        # Convert internal message format to Gemini types.Content
        contents = []
        for msg in messages:
            contents.append(
                types.Content(role=msg["role"], parts=[types.Part(text=msg["text"])])
            )
            
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                max_output_tokens=4096,
            ),
        )
        return response.text.strip()

class GroqProvider(LLMProvider):
    """Groq provider via groq SDK."""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)

    def generate_content(self, system_instruction: str, messages: List[Dict[str, str]]) -> str:
        if not self.client:
            raise ValueError("Groq API key not configured properly.")
            
        # Convert internal message format to Groq messages
        groq_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            role = "assistant" if msg["role"] == "model" else msg["role"]
            groq_messages.append({"role": role, "content": msg["text"]})
            
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=groq_messages,
            temperature=0.1,
            max_tokens=4096,
        )
        return response.choices[0].message.content.strip()


# Factory
def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "groq":
        return GroqProvider()
    else:
        # Extensible to OpenRouter, Groq, etc.
        # Fallback to Gemini for now
        return GeminiProvider()
