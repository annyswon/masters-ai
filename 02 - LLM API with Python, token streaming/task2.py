from openai import OpenAI
import os

OPENAI_API_KEY = YOUR_OPENAPI_API_KEY_HERE
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# openai client instance, by default it takes apikey from env above
client = OpenAI()

transcript_file = open("transcript.txt", "rb")

prompt_for_transcipt = f"Transcript following text in a blogpost format of 2-3 minutes reading time:\n\n{transcript_file.read()}"
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": prompt_for_transcipt}
    ]
)

print(completion.choices[0].message.content)