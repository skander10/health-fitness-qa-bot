#Schritt 2 — backend/main.py
#Das ist die eigentliche FastAPI-App 
# sie definiert einen Endpunkt (eine URL wie /ask), die von außen aufrufbar ist. 
# Wenn jemand (später unser React-Frontend) eine POST-Anfrage an /ask schickt mit einer Frage,
# ruft FastAPI unsere ask_agent()-Funktion aus agent.py auf und schickt die Antwort zurück.


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_agent

app = FastAPI()

# Erlaubt Anfragen vom React-Frontend (läuft während der Entwicklung meist auf Port 3000 oder 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # für die Entwicklung offen; für echtes Deployment würden wir das später einschränken
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic-Modell: legt fest, wie eine eingehende Anfrage aussehen MUSS (Validierung passiert automatisch)
class QuestionRequest(BaseModel):
    question: str
    thread_id: str


@app.post("/ask")
def ask(request: QuestionRequest) -> dict:
    answer = ask_agent(request.question, thread_id=request.thread_id)
    return {"answer": answer}


@app.get("/")
def health_check() -> dict:
    return {"status": "ok"}