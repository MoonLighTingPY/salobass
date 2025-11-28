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
        self.pause_wake_word = False  # Add flag to temporarily pause wake word detection
    
    def wants_opus(self) -> bool:
        """Return False to receive PCM audio instead of Opus."""
        return False
    
    def write(self, user, data):
        """Called when audio data is received from a user."""
        # Debug: check if write is being called
        if self.is_capturing:
            print(f"📥 Received audio packet: {len(data.pcm)} bytes from {user}")
        
        # Pass audio data to wake word service for processing (only if not paused)
        if not self.pause_wake_word:
            wake_word_service.process_audio_packet(user, data.pcm)
        
        # If we're capturing for speech recognition, buffer the audio
        if self.is_capturing:
            processed_audio = speech_service.process_discord_audio(data.pcm)
            if processed_audio:
                self.audio_buffer.append(processed_audio)
                print(f"✅ Buffered {len(processed_audio)} bytes (total: {sum(len(x) for x in self.audio_buffer)} bytes)")
    
    def pause_wake_word_detection(self):
        """Temporarily pause wake word detection (during capture/response)."""
        self.pause_wake_word = True
        print("⏸️ Wake word detection paused")
    
    def resume_wake_word_detection(self):
        """Resume wake word detection."""
        self.pause_wake_word = False
        # Clear the wake word service buffer to start fresh
        wake_word_service.audio_buffer = []
        print("▶️ Wake word detection resumed")
    
    def start_capture(self):
        """Start capturing audio for speech recognition."""
        self.is_capturing = True
        self.audio_buffer = []
        self.pause_wake_word_detection()  # Pause wake word during capture
        print("🎤 Started capturing audio for speech recognition")
    
    def stop_capture(self) -> bytes:
        """Stop capturing and return the buffered audio."""
        self.is_capturing = False
        audio_data = b''.join(self.audio_buffer)
        self.audio_buffer = []
        print(f"🎤 Stopped capturing, got {len(audio_data)} bytes of audio")
        # Don't resume wake word here - wait until response is complete
        return audio_data
    
    def cleanup(self):
        """Called when the sink is being cleaned up."""
        self.is_capturing = False
        self.audio_buffer = []
        self.resume_wake_word_detection()


class VoiceAssistantCommand(Command):
    """Command to start/stop voice assistant with streaming support."""
    
    def __init__(self):
        super().__init__("voice", "Start or stop voice assistant with streaming")
        self.active_guilds = {}  # guild_id -> AudioSink
        self.capture_duration = 5  # seconds to capture audio after wake word
        self.is_responding = {}  # guild_id -> bool (track if bot is responding)
        self.stop_response = {}  # guild_id -> bool (flag to stop current response)
        self.ai_task = {}  # guild_id -> Task (track AI generation task)
    
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
                if message.guild.id in self.is_responding:
                    del self.is_responding[message.guild.id]
                if message.guild.id in self.stop_response:
                    del self.stop_response[message.guild.id]
                if message.guild.id in self.ai_task:
                    # Cancel AI task if running
                    if not self.ai_task[message.guild.id].done():
                        self.ai_task[message.guild.id].cancel()
                    del self.ai_task[message.guild.id]
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
            voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
        
        if not isinstance(voice_client, voice_recv.VoiceRecvClient):
            await message.reply("❌ Voice client doesn't support receiving audio. Try disconnecting and running the command again.")
            return
        
        # Initialize flags
        self.is_responding[message.guild.id] = False
        self.stop_response[message.guild.id] = False
        
        # Create audio sink
        sink = StreamingAudioSink()
        
        # Define wake word detection callback with interruption support
        async def on_wake_word_detected():
            guild_id = message.guild.id
            
            # Check if bot is currently responding
            if self.is_responding.get(guild_id, False):
                print(f"🛑 Interruption detected in guild {guild_id}")
                # Set stop flag and stop current playback
                self.stop_response[guild_id] = True
                if voice_client.is_playing():
                    voice_client.stop()
                
                # Cancel the AI generation task if it's running
                if guild_id in self.ai_task and not self.ai_task[guild_id].done():
                    print("🛑 Cancelling AI generation task")
                    self.ai_task[guild_id].cancel()
                    try:
                        await self.ai_task[guild_id]
                    except asyncio.CancelledError:
                        print("✅ AI generation task cancelled")
                
                # Wait a moment for cleanup
                await asyncio.sleep(0.3)
                # Reset flags and resume wake word detection
                self.is_responding[guild_id] = False
                self.stop_response[guild_id] = False
                sink.resume_wake_word_detection()  # Add this
                print("✅ Interruption handled, processing new command...")
                # Fall through to start processing the new command
            
            print(f"🔔 Wake word detected in guild {guild_id}")
            
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
            
            # Resume wake word detection immediately after capture
            sink.resume_wake_word_detection()
            
            if not audio_data or len(audio_data) < 100:
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
                    # Mark as responding
                    self.is_responding[guild_id] = True
                    self.stop_response[guild_id] = False
                    
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
                        if not self.stop_response.get(guild_id, False):
                            await sentences_queue.put(sentence)
                            full_response.append(sentence)
                        else:
                            # If stopped, don't add more sentences
                            print(f"⏭️ Skipping sentence due to interruption: {sentence[:50]}...")
                    
                    # Start TTS playback task
                    async def tts_player():
                        """Play sentences as they arrive."""
                        while True:
                            try:
                                # Check stop flag before getting next sentence
                                if self.stop_response.get(guild_id, False):
                                    print("🛑 Stopping TTS playback due to interruption")
                                    # Drain the queue to clean up
                                    while not sentences_queue.empty():
                                        try:
                                            sentences_queue.get_nowait()
                                        except:
                                            break
                                    break
                                
                                sentence = await asyncio.wait_for(
                                    sentences_queue.get(),
                                    timeout=30.0
                                )
                                if sentence is None:  # End signal
                                    break
                                
                                # Check stop flag before playing
                                if self.stop_response.get(guild_id, False):
                                    break
                                
                                # Wait for current audio to finish (but check for interruption)
                                while voice_client.is_playing() and not self.stop_response.get(guild_id, False):
                                    await asyncio.sleep(0.1)
                                
                                if self.stop_response.get(guild_id, False):
                                    break
                                
                                # Stream the sentence to voice channel
                                await tts_service.stream_to_voice_channel(
                                    voice_client,
                                    sentence,
                                    lang="uk"
                                )
                                
                            except asyncio.TimeoutError:
                                break
                            except Exception as e:
                                print(f"❌ Error in TTS player: {e}")
                                break
                    
                    # Start TTS player in background
                    tts_task = asyncio.create_task(tts_player())
                    
                    # AI generation task (so we can cancel it)
                    async def ai_generator():
                        """Generate AI response."""
                        try:
                            await ai_service.get_response_with_sentence_streaming(
                                messages,
                                on_sentence,
                                system_prompt
                            )
                        except asyncio.CancelledError:
                            print("🛑 AI generation cancelled")
                            raise
                        except Exception as e:
                            if not self.stop_response.get(guild_id, False):
                                print(f"❌ Error during streaming: {e}")
                                raise
                    
                    # Start AI generation and track it
                    ai_gen_task = asyncio.create_task(ai_generator())
                    self.ai_task[guild_id] = ai_gen_task
                    
                    # Wait for AI generation to complete (or be cancelled)
                    try:
                        await ai_gen_task
                    except asyncio.CancelledError:
                        print("🛑 AI generation was cancelled")
                        # Make sure we signal end to TTS task
                        await sentences_queue.put(None)
                    
                    # Signal end of sentences (only if not stopped)
                    if not self.stop_response.get(guild_id, False):
                        await sentences_queue.put(None)
                    
                    # Wait for TTS to finish (with timeout to prevent hanging)
                    try:
                        await asyncio.wait_for(tts_task, timeout=60.0)
                    except asyncio.TimeoutError:
                        print("⏱️ TTS task timed out")
                        tts_task.cancel()
                    
                    # Add complete response to conversation history (only if not interrupted)
                    if not self.stop_response.get(guild_id, False) and full_response:
                        complete_response = " ".join(full_response)
                        chat_manager.add_assistant_message(message.author.id, complete_response)
                        print(f"🤖 AI response: {complete_response[:100]}...")
                    else:
                        print("🛑 Response was interrupted, not saving to history")
                    
                except asyncio.CancelledError:
                    print("🛑 Voice assistant task was cancelled")
                except Exception as e:
                    print(f"❌ Error getting AI response: {e}")
                    if not self.stop_response.get(guild_id, False):
                        error_response = "Вибачте, сталася помилка."
                        await tts_service.stream_to_voice_channel(
                            voice_client,
                            error_response,
                            lang="uk"
                        )
                finally:
                    # Clean up AI task reference
                    if guild_id in self.ai_task:
                        del self.ai_task[guild_id]
                    # Reset responding flag
                    self.is_responding[guild_id] = False
                    self.stop_response[guild_id] = False
                    # Resume wake word detection after response is complete
                    sink.resume_wake_word_detection()
                    print("✅ Ready for next command")
        
        # Get the current event loop and set callback
        loop = asyncio.get_event_loop()
        wake_word_service.set_detection_callback(on_wake_word_detected, loop)
        
        # Start wake word detection
        if wake_word_service.start_listening():
            voice_client.listen(sink)
            
            self.active_guilds[message.guild.id] = sink
            await message.reply(
                "🎤 **Streaming Voice Assistant Started!**\n\n"
                "Say **'Ok Salo'** in Discord voice chat to activate.\n"
                "After activation, speak your message (5 seconds).\n"
                "Say **'Ok Salo'** again while I'm speaking to interrupt and give a new command.\n\n"
                "Use `s!voice stop` to stop the assistant."
            )
        else:
            await message.reply("❌ Failed to start voice assistant. Check console for errors.")