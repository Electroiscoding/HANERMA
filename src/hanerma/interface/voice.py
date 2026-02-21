import asyncio
import queue
import threading
import numpy as np
import pyaudio
from faster_whisper import WhisperModel
from hanerma.orchestrator.nlp_compiler import compile_and_spawn

class VoiceHandler:
    """
    Lightweight local Speech-to-Text using Faster-Whisper.
    """
    
    def __init__(self):
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        self.audio_queue = queue.Queue()
        self.is_listening = False
    
    def listen_continuous(self):
        """
        Keeps mic open, converts audio to text, pipes to NLP compiler.
        """
        self.is_listening = True
        
        def audio_callback(in_data, frame_count, time_info, status):
            audio_np = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
            self.audio_queue.put(audio_np)
            return (in_data, pyaudio.paContinue)
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
            stream_callback=audio_callback
        )
        
        stream.start_stream()
        
        try:
            buffer = []
            while self.is_listening:
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                    buffer.append(audio_chunk)
                    
                    # Process every 5 seconds of audio
                    if len(buffer) * 1024 / 16000 > 5:
                        audio_combined = np.concatenate(buffer)
                        segments, _ = self.model.transcribe(audio_combined, language="en")
                        text = " ".join([segment.text for segment in segments])
                        
                        if text.strip():
                            print(f"[VOICE] Transcribed: {text}")
                            # Pipe to NLP compiler
                            app = compile_and_spawn(text)
                            asyncio.run(app.run())
                        
                        buffer = []
                        
                except queue.Empty:
                    continue
                    
        except KeyboardInterrupt:
            print("[VOICE] Stopped listening")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

class MultimodalObserver:
    """
    Multimodal Observer tool for images using local Vision model.
    """
    
    def observe(self, image_path: str) -> str:
        """
        Takes image file path, sends to local Vision model (e.g., LLaVA), returns description.
        """
        import base64
        import requests
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Assume local LLaVA API
        response = requests.post(
            "http://localhost:7860/api/predict",  # Assuming LLaVA web UI or API
            json={
                "data": [image_data, "Describe this image in detail."]
            }
        )
        response.raise_for_status()
        description = response.json()["data"][0]
        return description
