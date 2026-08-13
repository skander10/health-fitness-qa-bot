#Schritt 2 — backend/main.py
#Das ist die eigentliche FastAPI-App 
# sie definiert einen Endpunkt (eine URL wie /ask), die von außen aufrufbar ist. 
# Wenn jemand (später unser React-Frontend) eine POST-Anfrage an /ask schickt mit einer Frage,
# ruft FastAPI unsere ask_agent()-Funktion aus agent.py auf und schickt die Antwort zurück.


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_agent
from config import collection
from tools import extract_recipe_nutrition

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    thread_id: str
    topic: str
    video_id: str | None = None  # optional -- leer = über alle Videos des Topics suchen (Item 9)


@app.post("/ask")
def ask(request: QuestionRequest) -> dict:
    answer = ask_agent(
        request.question,
        thread_id=request.thread_id,
        topic=request.topic,
        video_id=request.video_id,
    )
    return {"answer": answer}


@app.get("/topics")
def list_topics() -> dict:
    """Gibt alle Topics zurück, die aktuell in der Collection gespeichert sind."""
    all_metadata = collection.get(include=["metadatas"])["metadatas"]
    topics = sorted(set(m["topic"] for m in all_metadata if "topic" in m))
    return {"topics": topics}


@app.get("/topics/{topic}/videos")
def list_videos_for_topic(topic: str) -> dict:
    """Gibt alle Videos zurück, die zu einem bestimmten Topic bereits gespeichert sind."""
    results = collection.get(include=["metadatas"], where={"topic": topic})
    seen = {}
    for m in results["metadatas"]:
        vid = m.get("video_id")
        if vid and vid not in seen:
            seen[vid] = m.get("title", vid)
    videos = [{"video_id": vid, "title": title} for vid, title in seen.items()]
    return {"videos": videos}


@app.get("/videos/{video_id}/recipe-summary")
def get_recipe_summary(video_id: str) -> dict:
    """Schätzt Zutaten, Zubereitung und Nährwerte eines Rezepts direkt aus dem Video-Transcript (LLM, keine externe Nährwert-API)."""
    summary = extract_recipe_nutrition(video_id)
    return {
        **summary.model_dump(),
        "disclaimer": "Geschätzt durch KI-Analyse des Video-Transcripts, keine geprüfte Nährwertangabe",
    }


@app.get("/")
def health_check() -> dict:
    return {"status": "ok"}