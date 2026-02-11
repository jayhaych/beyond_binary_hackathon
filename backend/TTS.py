from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import os
from elevenlabs import save

load_dotenv()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

audio = elevenlabs.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)

save(audio, "test_output.mp3")
print("Audio saved to test_output.mp3! Open the file to listen.") #ok this works

