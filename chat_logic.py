"""Chat logic for managing conversation history and context."""

from typing import Dict, List, Optional
from collections import deque
import discord


class ConversationHistory:
    """Manages conversation history for a user."""
    
    def __init__(self, max_messages: int = 10):
        """
        Initialize conversation history.
        
        Args:
            max_messages: Maximum number of messages to keep in history
        """
        self.messages: deque = deque(maxlen=max_messages)
        self.max_messages = max_messages
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender ('user' or 'assistant')
            content: The message content
        """
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def get_messages(self) -> List[dict]:
        """Get all messages in the conversation history."""
        return list(self.messages)
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()
    
    def is_empty(self) -> bool:
        """Check if the conversation history is empty."""
        return len(self.messages) == 0


class ChatManager:
    """Manages chat conversations for multiple users."""
    
    def __init__(self):
        """Initialize the chat manager."""
        self.conversations: Dict[int, ConversationHistory] = {}
        self.system_prompt = (
            "You are a helpful and friendly Discord bot assistant. "
            "You are part of a music bot called SaloBass (Сало-Басс, Ukrainian traditional dish and Bass). "
            "You always speak in Ukrainian, and NEVER in Russian, this is prohibited."
            "Be concise but informative in your responses. "
            "If asked about music commands, mention that users can use 's!help' to see available commands."
        )
    
    def get_conversation(self, user_id: int) -> ConversationHistory:
        """
        Get or create a conversation history for a user.
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            The conversation history for the user
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationHistory()
        return self.conversations[user_id]
    
    def add_user_message(self, user_id: int, message: str) -> None:
        """
        Add a user message to the conversation.
        
        Args:
            user_id: The Discord user ID
            message: The user's message
        """
        conversation = self.get_conversation(user_id)
        conversation.add_message("user", message)
    
    def add_assistant_message(self, user_id: int, message: str) -> None:
        """
        Add an assistant message to the conversation.
        
        Args:
            user_id: The Discord user ID
            message: The assistant's message
        """
        conversation = self.get_conversation(user_id)
        conversation.add_message("assistant", message)
    
    def get_messages_for_api(self, user_id: int) -> List[dict]:
        """
        Get formatted messages for API call.
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            List of messages formatted for the AI API
        """
        conversation = self.get_conversation(user_id)
        return conversation.get_messages()
    
    def clear_conversation(self, user_id: int) -> bool:
        """
        Clear a user's conversation history.
        
        Args:
            user_id: The Discord user ID
            
        Returns:
            True if conversation was cleared, False if no conversation existed
        """
        if user_id in self.conversations:
            self.conversations[user_id].clear()
            return True
        return False
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the AI."""
        return self.system_prompt
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set a custom system prompt for the AI."""
        self.system_prompt = prompt


# Global chat manager instance
chat_manager = ChatManager()
