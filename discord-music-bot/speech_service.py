"""Speech recognition service using Groq Whisper."""

import os
import tempfile
import pyaudio
import wave
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class SpeechService:
    """Service for speech recognition using Groq Whisper."""
    
    def __init__(self):
        """Initialize speech recognition service."""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Warning: GROQ_API_KEY not found in environment variables")
            self.client = None
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            self.model = "whisper-large-v3"
            print("✅ Speech recognition service initialized")
        except Exception as e:
            print(f"❌ Error initializing speech service: {e}")
            self.client = None
    
    async def record_audio(self, duration: int = 5, sample_rate: int = 16000) -> Optional[str]:
        """
        Record audio from microphone.
        
        Args:
            duration: Duration to record in seconds
            sample_rate: Sample rate for recording
            
        Returns:
            Path to temporary audio file, or None if recording failed
        """
        try:
            print(f"🎤 Recording for {duration} seconds...")
            
            pa = pyaudio.PyAudio()
            
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            frames = []
            for _ in range(0, int(sample_rate / 1024 * duration)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            
            wf = wave.open(temp_file.name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print(f"✅ Recording saved to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
            return None
    
    async def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio file using Groq Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text, or None if transcription failed
        """
        if not self.client:
            print("❌ Speech service not initialized")
            return None
        
        try:
            print("🔄 Transcribing audio...")
            
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_path, file.read()),
                    model=self.model,
                    temperature=0,
                    response_format="verbose_json",
                )
            
            text = transcription.text
            print(f"✅ Transcription: {text}")
            
            # Clean up temporary file
            try:
                os.remove(audio_path)
            except:
                pass
            
            return text
            
        except Exception as e:
            print(f"❌ Error transcribing audio: {e}")
            return None
    
    async def recognize_speech(self, duration: int = 5) -> Optional[str]:
        """
        Record and transcribe speech.
        
        Args:
            duration: Duration to record in seconds
            
        Returns:
            Transcribed text, or None if failed
        """
        audio_path = await self.record_audio(duration)
        if not audio_path:
            return None
        
        return await self.transcribe_audio(audio_path)


# Global speech service instance
speech_service = SpeechService()