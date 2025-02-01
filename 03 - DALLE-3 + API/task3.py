from openai import OpenAI
from IPython.display import Image, display
import time
import os

OPENAI_API_KEY = YOUR_OPENAPI_API_KEY_HERE
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# openai client instance, by default it takes apikey from env above
client = OpenAI()

prompt = input('What you wanna see? ')

styles = [
    'partying',
    'noir',
    'cinematic',
    'horror',
    'futuristic',
    'corporate',
    'baby',
    'cartoonish',
    '3d'
]

images_count = 0
while images_count < 9:
    try:
        response = client.images.generate(
            model="dall-e-2",
            prompt=f'{styles[images_count]} {prompt}',
            size="256x256",
            quality="standard",
            n=1,
        )
    
        for data in response.data:
            image_url = data.url
            print(f"URL: {image_url}")
            display(Image(url = image_url))
            images_count += 1

    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Trying to sleep for minute due limit")
        # limit for dall-e-2 - 5 images per minute, just wait for a minute 
        if images_count != 9:
           time.sleep(60)
