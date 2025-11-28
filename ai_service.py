"""AI service for chatbot functionality using Groq with streaming support."""

import os
import asyncio
from typing import Optional, AsyncGenerator, List, Dict
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class StreamingAIService:
    """Service for handling AI chat completions with streaming using Groq."""
    
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
            self.model = "llama-3.3-70b-versatile"
            self.max_tokens = 2048
            self.temperature = 1
            print("✅ Streaming AI service initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing AI service: {e}")
            self.client = None
    
    async def get_streaming_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Get a streaming response from the AI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to guide the AI behavior
            
        Yields:
            Chunks of the AI's response text as they're generated
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
            
            # Create streaming completion
            loop = asyncio.get_event_loop()
            
            # Use run_in_executor to avoid blocking
            def create_stream():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=chat_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=True,
                )
            
            stream = await loop.run_in_executor(None, create_stream)
            
            # Yield chunks as they arrive
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Error getting streaming AI response: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")
    
    async def get_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Get a complete response from the AI model.
        
        This method collects all streaming chunks and returns the full response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to guide the AI behavior
            
        Returns:
            The AI's complete response text
        """
        response_parts = []
        
        async for chunk in self.get_streaming_response(messages, system_prompt):
            response_parts.append(chunk)
        
        return "".join(response_parts)
    
    async def get_streaming_response_with_callback(
        self,
        messages: List[Dict[str, str]],
        on_chunk: callable,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Get a streaming response and call a callback for each chunk.
        
        Useful for processing chunks as they arrive (e.g., for TTS).
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            on_chunk: Callback function called with each chunk
            system_prompt: Optional system prompt to guide the AI behavior
            
        Returns:
            The AI's complete response text
        """
        response_parts = []
        
        async for chunk in self.get_streaming_response(messages, system_prompt):
            response_parts.append(chunk)
            await on_chunk(chunk)
        
        return "".join(response_parts)
    
    async def get_response_with_sentence_streaming(
        self,
        messages: List[Dict[str, str]],
        on_sentence: callable,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Get a streaming response and call a callback for each complete sentence.
        
        This is useful for TTS where you want to speak complete sentences
        as they're generated, providing a more natural streaming experience.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            on_sentence: Async callback function called with each sentence
            system_prompt: Optional system prompt to guide the AI behavior
            
        Returns:
            The AI's complete response text
        """
        response_parts = []
        sentence_buffer = ""
        sentence_endings = ('.', '!', '?')
        sentences_batch = []  # Collect multiple sentences
        target_batch_length = 100  # Target length for each speech chunk
        
        async for chunk in self.get_streaming_response(messages, system_prompt):
            response_parts.append(chunk)
            sentence_buffer += chunk
            
            for ending in sentence_endings:
                if ending in sentence_buffer:
                    parts = sentence_buffer.split(ending)
                    for i, part in enumerate(parts[:-1]):
                        sentence = part.strip() + ending
                        if sentence.strip():
                            sentences_batch.append(sentence.strip())
                            
                            # Send batch when it reaches target length
                            batch_text = " ".join(sentences_batch)
                            if len(batch_text) >= target_batch_length:
                                await on_sentence(batch_text)
                                sentences_batch = []
                    
                    sentence_buffer = parts[-1]
        
        # Handle remaining sentences
        if sentences_batch:
            await on_sentence(" ".join(sentences_batch))
        if sentence_buffer.strip():
            await on_sentence(sentence_buffer.strip())
        
        return "".join(response_parts)
    
    def set_model(self, model: str) -> None:
        """Change the AI model being used."""
        self.model = model
    
    def set_temperature(self, temperature: float) -> None:
        """Set the temperature for response generation (0.0 - 2.0)."""
        self.temperature = max(0.0, min(2.0, temperature))


# Alias for backward compatibility
class AIService(StreamingAIService):
    """Backward compatible alias for StreamingAIService."""
    pass


# Global AI service instance
try:
    ai_service = AIService() if os.getenv("GROQ_API_KEY") else None
    if ai_service and not hasattr(ai_service, 'client'):
        ai_service = None
except Exception as e:
    print(f"Failed to initialize AI service: {e}")
    ai_service = None
