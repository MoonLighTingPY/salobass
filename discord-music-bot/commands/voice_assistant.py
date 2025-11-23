"""Voice assistant command - wake word detection and voice interaction."""

from typing import List
import discord
import asyncio
from discord.ext import voice_recv
from commands.base_command import Command
from wake_word_service import wake_word_service
from speech_service import speech_service
from tts_service import tts_service
from ai_service import ai_service
from chat_logic import chat_manager


class AudioSink(voice_recv.AudioSink):
    """Custom audio sink to capture Discord voice data."""
    
    def __init__(self):
        super().__init__()
    
    def wants_opus(self) -> bool:
        """Return False to receive PCM audio instead of Opus."""
        return False
    
    def write(self, user, data):
        """Called when audio data is received from a user."""
        # Pass audio data to wake word service for processing
        wake_word_service.process_audio_packet(user, data.pcm)
    
    def cleanup(self):
        """Called when the sink is being cleaned up."""
        pass


class VoiceAssistantCommand(Command):
    """Command to start/stop voice assistant."""
    
    def __init__(self):
        super().__init__("voice", "Start or stop voice assistant")
        self.active_guilds = set()
    
    async def execute(self, message: discord.Message, args: List[str]) -> None:
        """Execute the voice assistant command."""
        if not message.guild:
            await message.reply("This command can only be used in a server!")
            return
        
        # Check if user wants to stop
        if args and args[0].lower() == "stop":
            if message.guild.id in self.active_guilds:
                # Stop listening
                voice_client = message.guild.voice_client
                if voice_client:
                    voice_client.stop_listening()
                
                wake_word_service.stop_listening()
                self.active_guilds.remove(message.guild.id)
                await message.reply("🔇 Voice assistant stopped!")
            else:
                await message.reply("❌ Voice assistant is not running!")
            return
        
        # Check if user is in voice channel
        if not message.author.voice or not message.author.voice.channel:
            await message.reply("❌ You need to be in a voice channel!")
            return
        
        # Check if already running
        if message.guild.id in self.active_guilds:
            await message.reply("ℹ️ Voice assistant is already running! Use `s!voice stop` to stop it.")
            return
        
        # Connect to voice channel with VoiceRecvClient
        voice_channel = message.author.voice.channel
        voice_client = message.guild.voice_client
        
        if not voice_client:
            # Connect with VoiceRecvClient for voice receiving support
            voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
        
        # Ensure we have a VoiceRecvClient instance
        if not isinstance(voice_client, voice_recv.VoiceRecvClient):
            await message.reply("❌ Voice client doesn't support receiving audio. Try disconnecting and running the command again.")
            return
        
        # Define wake word detection callback
        async def on_wake_word_detected():
            print(f"Wake word detected in guild {message.guild.id}")
            
            # Play beep sound
            await tts_service.play_beep(voice_client)
            
            # Record and transcribe speech (from local mic for now)
            text = await speech_service.recognize_speech(duration=5)
            
            if not text:
                response = "Вибачте, я не почув вас."
                audio_path = await tts_service.text_to_speech(response, lang="uk")
                if audio_path:
                    await tts_service.play_in_voice_channel(voice_client, audio_path)
                return
            
            # Get AI response
            if ai_service and ai_service.client:
                try:
                    # Add to conversation history
                    chat_manager.add_user_message(message.author.id, text)
                    
                    # Get messages and system prompt
                    messages = chat_manager.get_messages_for_api(message.author.id)
                    system_prompt = chat_manager.get_system_prompt()
                    
                    # Get AI response
                    ai_response = await ai_service.get_response(messages, system_prompt)
                    
                    # Add to conversation history
                    chat_manager.add_assistant_message(message.author.id, ai_response)
                    
                    # Convert to speech and play
                    audio_path = await tts_service.text_to_speech(ai_response, lang="uk")
                    if audio_path:
                        await tts_service.play_in_voice_channel(voice_client, audio_path)
                    
                except Exception as e:
                    print(f"Error getting AI response: {e}")
                    error_response = "Вибачте, сталася помилка."
                    audio_path = await tts_service.text_to_speech(error_response, lang="uk")
                    if audio_path:
                        await tts_service.play_in_voice_channel(voice_client, audio_path)
        
        # Get the current event loop and set callback
        loop = asyncio.get_event_loop()
        wake_word_service.set_detection_callback(on_wake_word_detected, loop)
        
        # Start wake word detection
        if wake_word_service.start_listening():
            # Start listening to Discord voice channel
            sink = AudioSink()
            voice_client.listen(sink)
            
            self.active_guilds.add(message.guild.id)
            await message.reply(
                "🎤 Voice assistant started!\n"
                "Say **'Ok Salo'** in Discord voice chat to activate.\n"
                "Use `s!voice stop` to stop the assistant."
            )
        else:
            await message.reply("❌ Failed to start voice assistant. Check console for errors.")