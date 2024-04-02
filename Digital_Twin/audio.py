import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play

def text_to_speech(response):
   
    client = ElevenLabs(
    api_key = os.environ.get("ELEVENLABS_KEY"),
    )

    voice_key = os.environ.get("VOICE_KEY")

    audio = client.generate(
        text = response,
        voice = voice_key,
        model = "eleven_multilingual_v2",
    )

    play(audio)
