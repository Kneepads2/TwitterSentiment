import asyncio
import nest_asyncio
from flask import Flask, request, render_template
from twikit import Client
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz
import openai
import os

app = Flask(__name__)

USERNAME = 'titanfail3'
EMAIL = 'dylant6649@gmail.com'
PASSWORD = 'Nimbus6649'

# Initialize client
client = Client('en-US')
executor = ThreadPoolExecutor(2)

# Apply nest_asyncio to allow nested event loops (if using nested async)
nest_asyncio.apply()

# Ensure OpenAI API key is set
openai.api_key = "your_openai_api_key_here"

def format_datetime(datetime_str, timezone='UTC'):
    dt = datetime.fromisoformat(datetime_str)
    dt = dt.astimezone(pytz.timezone(timezone))
    return dt.strftime("%B %d, %Y at %I:%M %p %Z")

async def fetch_tweets(query):
    client.load_cookies('cookies.json')
    tweets = await client.search_tweet(query, 'Top')
    tweet_list = []

    for tweet in tweets:
        tweet_container = {
            'name': tweet.user.name,
            'text': tweet.text,
            'created_at': format_datetime(str(tweet.created_at), timezone='America/Toronto'),  # Correct attribute usage
            'replies': tweet.replies,
            'reply_count': tweet.reply_count,
            'retweets': tweet.retweet_count,
            'likes': tweet.favorite_count
        }
        tweet_list.append(tweet_container)
        if len(tweet_list) > 100:  # Adjust the limit as needed
            break

    return tweet_list

def ai_prompt(data, query):
    prompt = f"""Based on this list of tweets, what is the general sentiment on {query}? Keep it short (1-2 paragraphs)
        {data}
    """

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    
    return response.choices[0].text.strip()

def run_async_fetch(query):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tweet_list = loop.run_until_complete(fetch_tweets(query))
    loop.close()
    return tweet_list

@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    tweet_list = []
    sentiment = ''
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            tweet_list = executor.submit(run_async_fetch, query).result()
            sentiment = ai_prompt(tweet_list, query)  # Get sentiment analysis

    return render_template('index2.html', tweet_list=tweet_list, sentiment=sentiment)

if __name__ == '__main__':
    app.run(debug=True)
