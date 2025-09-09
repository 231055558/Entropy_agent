from deepgram import DeepgramClient

# Initialize the client
deepgram = DeepgramClient("91b233deb692fcbc8f9f913ce3d300db65463450")  # Replace with your API key

from deepgram import LiveOptions, LiveTranscriptionEvents

# Create a websocket connection
connection = deepgram.listen.websocket.v("1")

# Handle transcription events
@connection.on(LiveTranscriptionEvents.Transcript)
def handle_transcript(result):
    print(result.channel.alternatives[0].transcript)

# Start connection with streaming options
connection.start(LiveOptions(model="nova-3", language="en-US"))

# Send audio data
connection.send(open("path/to/your/audio.wav", "rb").read())

# Close when done
connection.finish()