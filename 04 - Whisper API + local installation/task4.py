import random
from pydub import AudioSegment
from openai import OpenAI
import os

OPENAI_API_KEY = YOUR_OPENAPI_API_KEY_HERE
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# openai client instance, by default it takes apikey from env above
client = OpenAI()

input_file = "ITPU_MS_Degree_Session_5_Generative_AI_20241213_153714_Meeting_Recording.mp3"

audio = AudioSegment.from_mp3(input_file)

sample_duration_ms = 60 * 1000  # 1 minute

# Calculate the maximum possible start time to ensure a full 1-minute slice
max_start = len(audio) - sample_duration_ms

# Choose a random starting point between 0 and max_start (inclusive)
start_point = random.randint(0, max_start)
    
# Extract the 1-minute slice from the random start point
sample = audio[start_point:start_point + sample_duration_ms]

output_file = "tmp.mp3"

# Export the sample as an MP3 file
sample.export(output_file, format="mp3")

audio_file = open("tmp.mp3", "rb")

# Upload an opened file and transcript it with whisper
transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
)

print(transcription.text)