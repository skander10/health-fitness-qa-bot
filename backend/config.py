
#Enthält alles, was einmalig aufgebaut wird und von überall gebraucht wird:

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from langchain_openai import ChatOpenAI

load_dotenv(dotenv_path="../.env")
client = OpenAI()

chroma_client = chromadb.PersistentClient(path="../data/chroma_db")
collection = chroma_client.get_or_create_collection(name="health_fitness_videos")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

FINAL_VIDEO_ID = "E7W4OQfJWdw"