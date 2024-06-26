from gensim import corpora, models
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import nltk
import spacy
import requests
import time
loaded = False

def query(payload, API_URL, headers, max_retries=5):
    retries = 0
    while retries < max_retries:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            if "error" in error and "Model is loading" in error["error"]:
                print("Model is loading, waiting...")
                time.sleep(15)  # Wait for 15 seconds before retrying
                retries += 1
            else:
                # If the error is not related to model loading, break the loop and return the error
                return error
    return {"error": "Max retries exceeded or other error"}

def text_query(payload, API_URL, headers, max_retries=5):
    retries = 0
    while retries < max_retries:
        payload["parameters"] = {"max_length": 150}
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            if "error" in error and "Model is loading" in error["error"]:
                print("Model is loading, waiting...")
                time.sleep(15)  # Wait for 15 seconds before retrying
                retries += 1
            else:
                # If the error is not related to model loading, break the loop and return the error
                return error
    return {"error": "Max retries exceeded or other error"}


def topics(text):
    if text is None or len(text) == 0:
        return []  # Return an empty list or handle this case appropriately

    text = text.translate(str.maketrans('', '', string.punctuation))
    text = text.replace("\n", " ")
    text = text.lower()
    nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)
    nouns = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]
    nouns = set(nouns)

    # Check if the nouns are empty
    if len(nouns) == 0:
        return []  # Return an empty list or handle this case appropriately

    # create a dictionary from the text data
    dictionary = corpora.Dictionary([nouns])
    # create a corpus from the text data
    corpus = [dictionary.doc2bow(nouns)]

    # Check if the corpus is empty
    if len(corpus) == 0 or len(corpus[0]) == 0:
        return []  # Return an empty list or handle this case appropriately

    # train the LDA model on the corpus
    ldamodel = models.LdaModel(corpus, num_topics=3, id2word=dictionary)

    # extract the topics from the model
    topics = ldamodel.print_topics(num_topics=3, num_words=1)

    # print the topics
    topic_list = []
    for topic in topics:
        topic_list.append(topic[1].split('"')[1])

    return list(set(topic_list))




import requests
import time

import aiohttp
import asyncio


async def predict(text, feeling, stress_level, loaded=False):
    API_KEY = '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'
    MODEL_ID = 'DaJulster/Mental_health_identification'
    API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
    input_text = f"I am feeling: {feeling}. {text}" 
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with aiohttp.ClientSession() as session:
        async def query(payload, url, headers, isGen = 0):
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

        try:
            output = await query({"inputs": input_text}, API_URL, headers)
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(10)
            output = await query({"inputs": input_text}, API_URL, headers)

        score = None
        for item in output[0]:
            if item['label'] == 'NEGATIVE':
                score = item['score']

        if score is not None:
            score += 0.02 * stress_level
        print('---------DEBUG------------')
        print("Score as", score)
        print('---------DEBUG------------')
        return score
        
    
async def generate_good(text):
    API_KEY = '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'
    MODEL_ID = 'DaJulster/Mental_health_response'
    API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    topics = topics(text)

    tlist = ', '.join(topics)

    input_text = f"I am interested in {tlist}. {text}" 
    async with aiohttp.ClientSession() as session:
        async def text_query(payload, url, headers):
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

        try:
            output = await text_query({"inputs": input_text}, API_URL, headers)
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(10)
            output = await text_query({"inputs": input_text}, API_URL, headers)

        return output[0]['generated_text']

async def generate_bad(text, feeling):
    API_KEY = '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'
    MODEL_ID = 'DaJulster/Mental_health_response'
    API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
    input_text = f"I am feeling: {feeling}. {text}" 
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with aiohttp.ClientSession() as session:
        async def text_query(payload, url, headers, isGen = 1):
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

        try:
            output = await text_query({"inputs": input_text}, API_URL, headers)
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(10)
            output = await text_query({"inputs": input_text}, API_URL, headers)

        return output[0]['generated_text']

