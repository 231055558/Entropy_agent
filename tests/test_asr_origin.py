from deepgram import PrerecordedOptions
import os

from deepgram import DeepgramClient

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Initialize the client
deepgram = DeepgramClient(DEEPGRAM_API_KEY)  # Replace with your API key

response = deepgram.listen.rest.v("1").transcribe_url(
    source={"url": "https://dpgr.am/spacewalk.wav"},
    options=PrerecordedOptions(model="nova-3") # Apply other options
)
print(response)