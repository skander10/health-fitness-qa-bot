# Schritt 1 — backend/agent.py
# Das ist im Wesentlichen der Code aus M3 (Zellen 2, 4, 6, 8),
# Aber aufgeräumt in eine Funktion verpackt, die wir vom Backend aus aufrufen können.

import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

# .env liegt im Projekt-Root, backend/ ist eine Ebene tiefer
load_dotenv(dotenv_path="../.env")
client = OpenAI()

chroma_client = chromadb.PersistentClient(path="../data/chroma_db")
collection = chroma_client.get_or_create_collection(name="health_fitness_videos")


def embed_query(text: str) -> list:
    response = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return response.data[0].embedding


def search_video(query: str, n_results: int = 3) -> list:
    query_embedding = embed_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    matches = []
    for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
        matches.append({"text": doc, "start": metadata["start"], "end": metadata["end"]})
    return matches


@tool
def search_video_tool(query: str) -> str:
    """Durchsucht das Transcript des Videos nach Informationen zu einer bestimmten Frage oder einem Thema.
    Gib eine natürlichsprachliche Frage oder ein Stichwort ein. Gibt relevante Textausschnitte mit Zeitstempeln zurück."""
    results = search_video(query, n_results=3)
    formatted = ""
    for r in results:
        formatted += f"[{r['start']:.1f}s - {r['end']:.1f}s]: {r['text']}\n\n"
    return formatted


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [search_video_tool]
agent = create_agent(llm, tools)


def ask_agent(question: str) -> str:
    """Nimmt eine Frage entgegen, gibt sie an den Agenten, gibt nur die finale Textantwort zurück."""
    response = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return response["messages"][-1].content