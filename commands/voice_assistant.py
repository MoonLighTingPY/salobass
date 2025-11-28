"""Voice assistant command - wake word detection and streaming voice interaction."""

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


class StreamingAudioSink(voice_recv.AudioSink):
    """Custom audio sink to capture Discord voice data for streaming recognition."""
    
    def __init__(self, on_audio_callback=None):
        super().__init__()
        self.on_audio_callback = on_audio_callback
        self.is_capturing = False
        self.audio_buffer = []
    
    def wants_opus(self) -> bool:
        """Return False to receive PCM audio instead of Opus."""
        return False
    
    def write(self, user, data):
        """Called when audio data is received from a user."""
        # Pass audio data to wake word service for processing
        wake_word_service.process_audio_packet(user, data.pcm)
        
        # If we're capturing for speech recognition, also buffer the audio
        if self.is_capturing and self.on_audio_callback:
            processed_audio = speech_service.process_discord_audio(data.pcm)
            if processed_audio:
                self.audio_buffer.append(processed_audio)
    
    def start_capture(self):
        """Start capturing audio for speech recognition."""
        self.is_capturing = True
        self.audio_buffer = []
        print("🎤 Started capturing audio for speech recognition")
    
    def stop_capture(self) -> bytes:
        """Stop capturing and return the buffered audio."""
        self.is_capturing = False
        audio_data = b''.join(self.audio_buffer)
        self.audio_buffer = []
        print(f"🎤 Stopped capturing, got {len(audio_data)} bytes of audio")
        return audio_data
    
    def cleanup(self):
        """Called when the sink is being cleaned up."""
        self.is_capturing = False
        self.audio_buffer = []


class VoiceAssistantCommand(Command):
    """Command to start/stop voice assistant with streaming support."""
    
    def __init__(self):
        super().__init__("voice", "Start or stop voice assistant with streaming")
        self.active_guilds = {}  # guild_id -> AudioSink
        self.capture_duration = 5  # seconds to capture audio after wake word
    
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
                del self.active_guilds[message.guild.id]
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
        
        # Create audio sink with callback
        sink = StreamingAudioSink()
        
        # Define wake word detection callback with streaming response
        async def on_wake_word_detected():
            print(f"Wake word detected in guild {message.guild.id}")
            
            # Play beep sound
            await tts_service.play_beep(voice_client)
            
            # Wait for beep to finish
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
            
            # Start capturing audio from Discord
            sink.start_capture()
            
            # Capture audio for the configured duration
            await asyncio.sleep(self.capture_duration)
            
            # Stop capturing and get the audio
            audio_data = sink.stop_capture()
            
            if not audio_data or len(audio_data) < 1000:  # Too little audio
                response = "Вибачте, я не почув вас."
                await tts_service.stream_to_voice_channel(voice_client, response, lang="uk")
                return
            
            # Transcribe the captured audio
            text = await speech_service.transcribe_audio_data(audio_data)
            
            if not text:
                response = "Вибачте, я не почув вас."
                await tts_service.stream_to_voice_channel(voice_client, response, lang="uk")
                return
            
            print(f"📝 User said: {text}")
            
            # Get streaming AI response with sentence-by-sentence TTS
            if ai_service and ai_service.client:
                try:
                    # Add to conversation history
                    chat_manager.add_user_message(message.author.id, text)
                    
                    # Get messages and system prompt
                    messages = chat_manager.get_messages_for_api(message.author.id)
                    system_prompt = chat_manager.get_system_prompt()
                    
                    # Collect sentences for TTS
                    sentences_queue = asyncio.Queue()
                    full_response = []
                    
                    async def on_sentence(sentence: str):
                        """Queue sentence for TTS playback."""
                        await sentences_queue.put(sentence)
                        full_response.append(sentence)
                    
                    # Start TTS playback task
                    async def tts_player():
                        """Play sentences as they arrive."""
                        while True:
                            try:
                                sentence = await asyncio.wait_for(
                                    sentences_queue.get(),
                                    timeout=30.0
                                )
                                if sentence is None:  # End signal
                                    break
                                
                                # Wait for current audio to finish
                                while voice_client.is_playing():
                                    await asyncio.sleep(0.1)
                                
                                # Stream the sentence to voice channel
                                await tts_service.stream_to_voice_channel(
                                    voice_client,
                                    sentence,
                                    lang="uk"
                                )
                                
                            except asyncio.TimeoutError:
                                break
                            except Exception as e:
                                print(f"Error in TTS player: {e}")
                                break
                    
                    # Start TTS player in background
                    tts_task = asyncio.create_task(tts_player())
                    
                    # Get streaming response with sentence callbacks
                    await ai_service.get_response_with_sentence_streaming(
                        messages,
                        on_sentence,
                        system_prompt
                    )
                    
                    # Signal end of sentences
                    await sentences_queue.put(None)
                    
                    # Wait for TTS to finish
                    await tts_task
                    
                    # Add complete response to conversation history
                    complete_response = " ".join(full_response)
                    chat_manager.add_assistant_message(message.author.id, complete_response)
                    
                    print(f"🤖 AI response: {complete_response[:100]}...")
                    
                except Exception as e:
                    print(f"Error getting AI response: {e}")
                    error_response = "Вибачте, сталася помилка."
                    await tts_service.stream_to_voice_channel(
                        voice_client,
                        error_response,
                        lang="uk"
                    )
        
        # Get the current event loop and set callback
        loop = asyncio.get_event_loop()
        wake_word_service.set_detection_callback(on_wake_word_detected, loop)
        
        # Start wake word detection
        if wake_word_service.start_listening():
            # Start listening to Discord voice channel
            voice_client.listen(sink)
            
            self.active_guilds[message.guild.id] = sink
            await message.reply(
                "🎤 **Streaming Voice Assistant Started!**\n\n"
                "Say **'Ok Salo'** in Discord voice chat to activate.\n"
                "After activation, speak your message (5 seconds).\n"
                "The AI response will be streamed back as speech.\n\n"
                "Use `s!voice stop` to stop the assistant."
            )
        else:
            await message.reply("❌ Failed to start voice assistant. Check console for errors.")