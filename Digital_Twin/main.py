import numpy as np
import faiss
import pickle
import os
from openai import AzureOpenAI
import speech_recognition as sr
from pythonosc.udp_client import SimpleUDPClient
import sainsbury
import audio
import youtube
import pandas as pd
import numpy as np
import faiss
import glob
import pickle
import re

ip = "127.0.0.1"
port = 8003
osc_client = SimpleUDPClient(ip, port)  

def get_embeddings():
    df = pd.DataFrame(columns=['text'])
    path = 'more-knowledge/*.txt'

    for file in glob.glob(path):
        with open(file, 'r') as f:
            text = f.read()
        df = pd.concat([df, pd.DataFrame([{'text': text}])], ignore_index=True)

    embeddings = []
    for i in range(0, len(df), BATCH_SIZE := 4):
        batch_skills = df["text"].iloc[i:i + BATCH_SIZE].tolist()
        batch_embeddings = get_embedding_batch(batch_skills)
        embeddings.extend(batch_embeddings)

    df['embedding'] = embeddings

    embeddings = np.vstack(df['embedding'].values).astype('float32')

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, 'more-knowledge/knowledge_index')

    with open('more-knowledge/knowledge.pkl', 'wb') as f:
        pickle.dump(df['text'], f)

def extract_text_from_voice():
    recognizer = sr.Recognizer()
    while True:

        with sr.Microphone() as source:
            print("Hello Sensei, what is the mission?")        
            audio = recognizer.listen(source)
        try:
            texts = recognizer.recognize_google(audio)
            print(f"You said: {texts}")
            if "hello" in texts:
                osc_client.send_message("/pear", 124.0)
                print("osc signal sent")
            if "ingredients" in texts:
                osc_client.send_message("/grape", 123.0)
                print("osc signal sent")
                
            return texts

        except sr.UnknownValueError:
            print("Sorry, I could not understand your audio.")
        except sr.RequestError as e:
            print(f"Sorry, an error occurred: {str(e)}") 


def get_embedding(text_to_embed):
    response = client.embeddings.create(model=os.getenv("EMBEDDING_MODEL"), input=[text_to_embed])
    embedding = response.data[0].embedding

    return embedding

def load_index(pickle_path, faiss_path):
    with open(pickle_path, 'rb') as f:
        skills = pickle.load(f)
    index = faiss.read_index(faiss_path)

    return index, skills

def get_similarity(index, knowledge, query, k):
    embedding = np.array(get_embedding(query)).astype('float32')
    embedding = embedding.reshape(-1, embedding.shape[0])
    D, I = index.search(embedding, k=k)  
    indices = I[0]
    selected = ""

    for i in indices:
        selected += "\n" + knowledge.iloc[i]

    return selected

def get_embedding_batch(texts_to_embed):
    # Embed a batch of texts
    response = client.embeddings.create(model="text-embedding-ada-002", input=texts_to_embed)
    # Extract the AI output embeddings as lists of floats
    embeddings = [data.embedding for data in response.data]
    return embeddings


def contact_gpt(texts):  
    knowledge_index, knowledge = load_index("more-knowledge/knowledge.pkl", "more-knowledge/knowledge_index")
    context_text = get_similarity(knowledge_index, knowledge, texts, 3)
    context = [
        {"role": "system",
            "content": "You are my personal assistant. Please answer the questions based on the context provided. If the answer is not"
                    " contained within the text say \"This is not my purpose\"."
                    "\n Context: " + context_text + "\n Question: " + texts
            }
    ]

    response = client.chat.completions.create(
        model = "GPT-4",
        messages = context
    )

    answer = response.choices[0].message.content
    # with open("conversation\latest_response.txt", "w") as convo_file:
    #      convo_file.write(answer)
    print(answer)     
    return answer

if __name__ == "__main__":    
    client = AzureOpenAI(api_key=os.getenv("AZURE_OPENAI_KEY"),
                         azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                         api_version="2023-12-01-preview")
    
    get_embeddings()
    youtube.retrieve_playlist()
    keyword = "mission complete"
    command = ""
    
    while command != keyword:
        command = extract_text_from_voice()        
        if command != keyword:            
            gpt_response = contact_gpt(command)
            audio.text_to_speech(gpt_response)
            if "hello" in command:
                osc_client.send_message("/pear", 125.0)
                print("osc signal sent")
            if "ingredients" in command:
                osc_client = SimpleUDPClient(ip, port)  
                osc_client.send_message("/grape", 125.0)
                print("osc signal sent")
                ingredients_string = gpt_response
                pattern = '[0-9]'
                ingredients_list = ingredients_string.split(",")
                denumbered_list = [re.sub(pattern, '', i) for i in ingredients_list]
               
                print(denumbered_list)
            if "order" in command:
                sainsbury.order_ingredients(denumbered_list) 
        else:
             print("Goodbye Sensei!")