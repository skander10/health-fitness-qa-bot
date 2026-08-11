import json

from config import client, collection, llm, FINAL_VIDEO_ID
from langchain.tools import tool



from pydantic import BaseModel, Field


class FactCheckResult(BaseModel):
    bewertung: str = Field(
        description="Eine von: Weitgehend bestätigt, Teilweise bestätigt, Umstritten, Nicht ausreichend belegt"
    )
    begruendung: str = Field(description="2-3 Sätze, warum diese Bewertung zutrifft")

fact_check_llm = llm.with_structured_output(FactCheckResult)
# ---------- Grundbausteine ----------

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


def get_all_chunks_with_metadata() -> list:
    results = collection.get(include=["documents", "metadatas"])
    chunks = []
    for doc, metadata in zip(results["documents"], results["metadatas"]):
        chunks.append({"text": doc, "start": metadata["start"], "end": metadata["end"]})
    return chunks


def get_full_transcript_text() -> str:
    all_chunks = get_all_chunks_with_metadata()
    sorted_chunks = sorted(all_chunks, key=lambda c: c["start"])
    return "\n".join(chunk["text"] for chunk in sorted_chunks)


# ---------- Tool 1: RAG-Retrieval ----------

@tool
def search_video_tool(query: str) -> str:
    """Durchsucht das Transcript des Videos nach Informationen zu einer bestimmten Frage oder einem Thema.
    Gib eine natürlichsprachliche Frage oder ein Stichwort ein. Gibt relevante Textausschnitte mit Zeitstempeln zurück."""
    results = search_video(query, n_results=3)
    formatted = ""
    for r in results:
        formatted += f"[{r['start']:.1f}s - {r['end']:.1f}s]: {r['text']}\n\n"
    return formatted


# ---------- Tool 2: Multi-Query Retrieval ----------

def generate_query_variations(question: str, n_variations: int = 3) -> list:
    prompt = f"""Generate {n_variations} different ways to search for information related to this question.
Each variation should use different wording but search for the same underlying information.
Return ONLY the variations, one per line, no numbering, no extra text.

Question: {question}"""
    response = llm.invoke(prompt)
    variations = [line.strip() for line in response.content.split("\n") if line.strip()]
    return [question] + variations


@tool
def multi_query_search_tool(question: str) -> str:
    """Durchsucht das Video mit mehreren umformulierten Varianten der Frage für bessere Trefferquote.
    Nutze dieses Tool bei komplexeren oder vagen Fragen, wenn die einfache Suche evtl. nicht ausreicht."""
    queries = generate_query_variations(question)
    all_results = []
    seen_texts = set()
    for q in queries:
        for r in search_video(q, n_results=3):
            if r["text"] not in seen_texts:
                all_results.append(r)
                seen_texts.add(r["text"])
    formatted = ""
    for r in all_results:
        formatted += f"[{r['start']:.1f}s - {r['end']:.1f}s]: {r['text']}\n\n"
    return formatted


# ---------- Tool 3: Zeitstempel-Suche ----------

@tool
def search_by_timestamp_tool(seconds: float) -> str:
    """Findet den Videoausschnitt, der zu einem bestimmten Zeitpunkt (in Sekunden) gehört.
    Nutze dieses Tool, wenn der User nach einem konkreten Zeitpunkt fragt, z.B. 'Was wurde bei Minute 20 gesagt?'."""
    all_chunks = get_all_chunks_with_metadata()
    for chunk in all_chunks:
        if chunk["start"] <= seconds <= chunk["end"]:
            return f"[{chunk['start']:.1f}s - {chunk['end']:.1f}s]: {chunk['text']}"
    return "Kein Inhalt für diesen Zeitpunkt gefunden."


# ---------- Tool 4: Summary ----------

@tool
def summarize_video_tool(focus: str = "general") -> str:
    """Erstellt eine Zusammenfassung des gesamten Videos.
    Nutze dieses Tool, wenn der User um eine Zusammenfassung, einen Überblick, oder die Kernaussagen des Videos bittet.
    'focus' kann 'general' (allgemeiner Überblick) oder 'technical' (strukturierte Extraktion konkreter Details wie Zutaten, Dosierungen, Übungen) sein."""
    full_text = get_full_transcript_text()

    if focus == "technical":
        prompt = f"""Analysiere dieses Transcript und extrahiere die konkreten, umsetzbaren Informationen in strukturierter Form.
Falls es sich um ein Rezept handelt: liste Zutaten und Schritte.
Falls es sich um Nahrungsergänzungsmittel/Dosierungen handelt: liste Substanz, empfohlene Menge, und Kontext.
Falls es sich um Trainingsübungen handelt: liste Übung, Wiederholungen, Hinweise.
Bei anderen Inhalten: extrahiere die wichtigsten konkreten Fakten/Empfehlungen in Stichpunkten.

Transcript:
{full_text}"""
    else:
        prompt = f"""Fasse dieses Video in 3-5 Sätzen zusammen. Nenne die wichtigsten besprochenen Themen.

Transcript:
{full_text}"""

    response = llm.invoke(prompt)
    return response.content


# ---------- Tool 5: Metadata ----------

@tool
def get_video_metadata_tool() -> str:
    """Gibt Informationen über das Video selbst zurück: Titel, Kanal, Upload-Datum, Länge, Themen-Tags, Beschreibung.
    Nutze dieses Tool, wenn der User nach dem Video selbst fragt (nicht nach seinem Inhalt) --
    z.B. 'Wie heißt das Video?', 'Wie lang ist es?', 'Von wem ist es?', 'Worum geht es grob?'."""
    with open(f"../data/video_metadata/{FINAL_VIDEO_ID}.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    duration_min = metadata["duration_seconds"] // 60
    upload_date_formatted = f"{metadata['upload_date'][:4]}-{metadata['upload_date'][4:6]}-{metadata['upload_date'][6:]}"
    tags_str = ", ".join(metadata.get("tags", []))

    return (
        f"Titel: {metadata['title']}\n"
        f"Kanal: {metadata['channel']}\n"
        f"Hochgeladen am: {upload_date_formatted}\n"
        f"Länge: {duration_min} Minuten\n"
        f"Themen: {tags_str}\n"
        f"Beschreibung (Auszug): {metadata['description'][:300]}..."
    )


# ---------- Tool 6: Fact-Check ----------

@tool
def fact_check_tool(claim_or_topic: str) -> str:
    """Prüft eine Ernährungs-/Fitness-Behauptung aus dem Video auf wissenschaftliche Plausibilität.
    Nutze dieses Tool, wenn der User wissen will, ob etwas 'stimmt', 'wissenschaftlich belegt' ist,
    oder wie vertrauenswürdig eine Aussage im Video ist."""
    video_chunks = search_video(claim_or_topic, n_results=2)
    video_context = "\n".join(c["text"] for c in video_chunks)

    prompt = f"""Du bist ein wissenschaftlicher Fact-Checker im Bereich Ernährung/Fitness.

Folgende Aussage stammt aus einem YouTube-Video:
"{video_context}"

Bewerte diese Aussage anhand deines wissenschaftlichen Wissens."""

    result: FactCheckResult = fact_check_llm.invoke(prompt)

    return (
        f"BEWERTUNG: {result.bewertung}\n"
        f"BEGRÜNDUNG: {result.begruendung}\n"
        f"HINWEIS: Diese Einschätzung basiert auf allgemeinem KI-Wissen, nicht auf einer geprüften externen Datenbank."
    )

# Die fertige Liste, die agent.py importieren wird
all_tools = [
    search_video_tool,
    multi_query_search_tool,
    search_by_timestamp_tool,
    summarize_video_tool,
    get_video_metadata_tool,
    fact_check_tool,
]