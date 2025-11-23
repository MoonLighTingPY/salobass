"""Chat command - allows users to chat with AI."""

from typing import List
import discord
from commands.base_command import Command
from ai_service import ai_service
from chat_logic import chat_manager


class ChatCommand(Command):
    """Command that allows users to chat with AI using Groq."""
    
    def __init__(self):
        super().__init__("chat", "Chat with the AI assistant")
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the chat command."""
        # Check if AI service is available
        if not ai_service or not hasattr(ai_service, 'client') or not ai_service.client:
            await message.reply(
                "❌ AI service is not configured. Please set GROQ_API_KEY in your .env file.\n"
                "Get your API key from: https://console.groq.com/keys"
            )
            return
        
        # Check if user provided a message
        if not args:
            await message.reply(
                f"💬 **Chat Command Usage:**\n"
                f"• `s!chat <your message>` - Chat with the AI\n"
                f"• `s!chat clear` - Clear your conversation history\n"
                f"• `s!chat help` - Show this help message"
            )
            return
        
        # Handle special commands
        if args[0].lower() == "clear":
            cleared = chat_manager.clear_conversation(message.author.id)
            if cleared:
                await message.reply("✅ Your conversation history has been cleared!")
            else:
                await message.reply("ℹ️ You don't have any conversation history yet.")
            return
        
        if args[0].lower() == "help":
            await message.reply(
                f"💬 **Chat Command Help:**\n\n"
                f"**Usage:**\n"
                f"• `s!chat <message>` - Send a message to the AI\n"
                f"• `s!chat clear` - Clear your conversation history\n\n"
                f"**Features:**\n"
                f"• The AI remembers your last 10 messages\n"
                f"• Each user has their own conversation history\n"
                f"• Powered by Groq AI (llama-3.1-8b-instant)\n\n"
                f"**Examples:**\n"
                f"• `s!chat Hello, how are you?`\n"
                f"• `s!chat What commands does this bot have?`\n"
                f"• `s!chat Tell me a joke`"
            )
            return
        
        # Join all args as the user's message
        user_message = " ".join(args)
        
        # Show typing indicator
        async with message.channel.typing():
            try:
                # Add user message to conversation history
                chat_manager.add_user_message(message.author.id, user_message)
                
                # Get conversation history
                messages = chat_manager.get_messages_for_api(message.author.id)
                system_prompt = chat_manager.get_system_prompt()
                
                # Get AI response
                ai_response = await ai_service.get_response(messages, system_prompt)
                
                # Add assistant response to conversation history
                chat_manager.add_assistant_message(message.author.id, ai_response)
                
                # Split response if it's too long (Discord limit is 2000 characters)
                if len(ai_response) > 1900:
                    chunks = [ai_response[i:i+1900] for i in range(0, len(ai_response), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(ai_response)
                
            except Exception as e:
                error_message = str(e)
                if "api_key" in error_message.lower() or "authentication" in error_message.lower():
                    await message.reply(
                        "❌ Authentication error with Groq API. Please check your GROQ_API_KEY in .env file."
                    )
                elif "rate limit" in error_message.lower():
                    await message.reply(
                        "⏱️ Rate limit exceeded. Please wait a moment and try again."
                    )
                else:
                    await message.reply(
                        f"❌ An error occurred while processing your message.\n"
                        f"Error: {error_message}"
                    )
                print(f"Error in chat command: {e}")
