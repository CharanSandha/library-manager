from dotenv import load_dotenv
import os
from openai import OpenAI


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = api_key)

messages = [
    {"role": "system", "content": "You are a helpful assistant who has great knowledge about the details of various books. Return ouputs of genre and year with a comma in between that's it."}
]
def determine_genre_and_year(title, author):
    user_input = f"What is the genre and year published of '{title}' by '{author}'"
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )

    reply = response.choices[0].message.content
    
    if reply and "," in reply:
        genre, year = [x.strip() for x in reply.split(",", 1)]
        if year.isdigit() and len(year) == 4:
            return genre, int(year)
    # fallback default values instead of None
    return "Unknown Genre", 0


    