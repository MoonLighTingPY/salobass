"""AI service for chatbot functionality using Groq."""

import os
import asyncio
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIService:
    """Service for handling AI chat completions using Groq."""
    
    def __init__(self):
        """Initialize the AI service with Groq client."""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found in environment variables")
            self.client = None
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            # Using llama-3.1-8b-instant for fast responses
            self.model = "llama-3.1-8b-instant"
            self.max_tokens = 1024
            self.temperature = 0.7
            print("✅ AI service initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing AI service: {e}")
            self.client = None
    
    async def get_response(self, messages: list, system_prompt: Optional[str] = None) -> str:
        """
        Get a response from the AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to guide the AI behavior
            
        Returns:
            The AI's response text
        """
        if not self.client:
            raise Exception("AI service is not properly configured")
        
        try:
            # Prepare messages with optional system prompt
            chat_messages = []
            
            if system_prompt:
                chat_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            chat_messages.extend(messages)
            
            # Run the blocking Groq call in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=chat_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")
    
    def set_model(self, model: str) -> None:
        """Change the AI model being used."""
        self.model = model
    
    def set_temperature(self, temperature: float) -> None:
        """Set the temperature for response generation (0.0 - 2.0)."""
        self.temperature = max(0.0, min(2.0, temperature))


# Global AI service instance
try:
    ai_service = AIService() if os.getenv("GROQ_API_KEY") else None
    if ai_service and not hasattr(ai_service, 'client'):
        ai_service = None
except Exception as e:
    print(f"Failed to initialize AI service: {e}")
    ai_service = None
