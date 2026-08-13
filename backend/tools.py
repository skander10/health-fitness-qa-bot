import json
import re


from config import client, collection, llm, FINAL_VIDEO_ID, nutrition_kb_collection, tavily_client
from langchain.tools import tool



from pydantic import BaseModel, Field


class FactCheckResult(BaseModel):
    bewertung: str = Field(
        description="Eine von: Weitgehend bestätigt, Teilweise bestätigt, Umstritten, Nicht ausreichend belegt"
    )
    begruendung: str = Field(description="2-3 Sätze, warum diese Bewertung zutrifft")

fact_check_llm = llm.with_structured_output(FactCheckResult)

PRIORITY_TOPICS_WITH_KB = {"health"}  # später erweiterbar, z.B. + "sport"

# ---------- Grundbausteine ----------

def embed_query(text: str) -> list:
    response = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return response.data[0].embedding


def search_video(query: str, n_results: int = 3, topic: str = None, video_id: str = None) -> list:
    query_embedding = embed_query(query)

    # Filter dynamisch aufbauen: video_id (spezifisch) ODER topic (mehrere Videos desselben Themas)
    where_filter = None
    if video_id:
        where_filter = {"video_id": video_id}
    elif topic:
        where_filter = {"topic": topic}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
    )
    matches = []
    for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
        matches.append({"text": doc, "start": metadata["start"], "end": metadata["end"]})
    return matches







def add_knowledge_entry(text: str, source: str, topic: str, entry_id: str) -> None:
    embedding = embed_query(text)
    nutrition_kb_collection.upsert(
        ids=[entry_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"source": source, "topic": topic}],
    )

def search_web_for_health_fact(query: str) -> str:
    response = tavily_client.search(
        query=f"{query} nutrition health scientific evidence",
        max_results=3,
        include_answer=True,
    )

    if response.get("answer"):
        return response["answer"]

    # Fallback: falls Tavily keine direkte Zusammenfassung liefert, Ergebnisse manuell zusammenfassen
    snippets = [r["content"][:300] for r in response.get("results", [])]
    return "\n".join(snippets) if snippets else ""

def search_nutrition_kb(query: str, topic: str = "health", n_results: int = 2, max_distance: float = 0.8) -> list:
    query_embedding = embed_query(query)
    results = nutrition_kb_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"topic": topic},
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    for doc, metadata, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        if distance <= max_distance:
            matches.append({"text": doc, "source": metadata["source"]})
    return matches



def clean_fact_check_format(answer: str) -> str:
    """Entfernt Freitext vor 'BEWERTUNG:', falls das LLM trotz system_prompt etwas davorsetzt.
    Greift nur bei Fact-Check-Antworten, andere Tools bleiben unangetastet."""
    if "BEWERTUNG:" in answer:
        match = re.search(r"BEWERTUNG:.*", answer, re.DOTALL)
        if match:
            return match.group(0)
    return answer


def get_all_chunks_with_metadata(topic: str = None, video_id: str = None) -> list:
    where_filter = None
    if video_id:
        where_filter = {"video_id": video_id}
    elif topic:
        where_filter = {"topic": topic}

    results = collection.get(include=["documents", "metadatas"], where=where_filter)
    chunks = []
    for doc, metadata in zip(results["documents"], results["metadatas"]):
        chunks.append({"text": doc, "start": metadata["start"], "end": metadata["end"]})
    return chunks


def get_full_transcript_text(topic: str = None, video_id: str = None) -> str:
    all_chunks = get_all_chunks_with_metadata(topic=topic, video_id=video_id)
    sorted_chunks = sorted(all_chunks, key=lambda c: c["start"])
    return "\n".join(chunk["text"] for chunk in sorted_chunks)



def generate_query_variations(question: str, n_variations: int = 3) -> list:
    prompt = f"""Generate {n_variations} different ways to search for information related to this question.
Each variation should use different wording but search for the same underlying information.
Return ONLY the variations, one per line, no numbering, no extra text.

Question: {question}"""
    response = llm.invoke(prompt)
    variations = [line.strip() for line in response.content.split("\n") if line.strip()]
    return [question] + variations



def make_tools(topic: str = None, video_id: str = None) -> list:
    """Baut alle 6 Tools frisch, mit topic/video_id fest eingebettet (Closure).
    So muss das LLM diese IDs nie selbst raten oder im Prompt mitschicken -- 
    verhindert Fehler durch falsche/erfundene IDs."""


# ---------- Tool 1: RAG-Retrieval ----------

    @tool
    def search_video_tool(query: str) -> str:
        """Durchsucht das Transcript nach Informationen zu einer Frage oder einem Thema.
        Gib eine natürlichsprachliche Frage oder ein Stichwort ein."""
        results = search_video(query, n_results=3, topic=topic, video_id=video_id)
        formatted = ""
        for r in results:
            formatted += f"[{r['start']:.1f}s - {r['end']:.1f}s]: {r['text']}\n\n"
        return formatted

    # ---------- Tool 2: Multi-Query Retrieval ----------


    @tool
    def multi_query_search_tool(question: str) -> str:
        """Durchsucht mit mehreren umformulierten Varianten der Frage für bessere Trefferquote."""
        queries = generate_query_variations(question)
        all_results = []
        seen_texts = set()
        for q in queries:
            for r in search_video(q, n_results=3, topic=topic, video_id=video_id):
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
        """Findet den Videoausschnitt, der zu einem bestimmten Zeitpunkt (in Sekunden) gehört."""
        all_chunks = get_all_chunks_with_metadata(topic=topic, video_id=video_id)
        for chunk in all_chunks:
            if chunk["start"] <= seconds <= chunk["end"]:
                return f"[{chunk['start']:.1f}s - {chunk['end']:.1f}s]: {chunk['text']}"
        return "Kein Inhalt für diesen Zeitpunkt gefunden."

    # ---------- Tool 4: Summary ----------


    @tool
    def summarize_video_tool(focus: str = "general") -> str:
        """Erstellt eine Zusammenfassung des Videos. 'focus': 'general' oder 'technical'."""
        full_text = get_full_transcript_text(topic=topic, video_id=video_id)
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
        """Gibt Informationen über das Video zurück: Titel, Kanal, Upload-Datum, Länge, Themen-Tags."""
        target_video_id = video_id or FINAL_VIDEO_ID
        with open(f"../data/video_metadata/{target_video_id}.json", "r", encoding="utf-8") as f:
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
        """Prüft eine Ernährungs-/Fitness-Behauptung aus dem Video auf wissenschaftliche Plausibilität."""
        video_chunks = search_video(claim_or_topic, n_results=2, topic=topic, video_id=video_id)
        video_context = "\n".join(c["text"] for c in video_chunks)

        if not video_context.strip():
            video_context = "(Das Video behandelt dieses Thema nicht bzw. es gibt keinen thematisch passenden Ausschnitt.)"

        if topic in PRIORITY_TOPICS_WITH_KB:
            kb_matches = search_nutrition_kb(claim_or_topic, topic=topic)
        else:
            kb_matches = []  # Nicht-Priority-Topic -> direkt zu Websuche-Fallback in der bestehenden 3-Stufen-Kette
        if kb_matches:
            evidence = "\n".join(m["text"] for m in kb_matches)
            sources = ", ".join(set(m["source"] for m in kb_matches))
            evidence_note = f"Quelle: Kuratierte Wissensdatenbank ({sources})"
        else:
            web_result = search_web_for_health_fact(claim_or_topic)
            if web_result:
                evidence = web_result
                evidence_note = "Quelle: Live-Websuche (Tavily) -- nicht manuell kuratiert, Ergebnis kann variieren"
            else:
                evidence = None
                evidence_note = "Quelle: Allgemeines KI-Wissen -- weder Wissensdatenbank noch Websuche lieferten ein Ergebnis"

        if evidence:
            prompt = f"""Du bist ein wissenschaftlicher Fact-Checker im Bereich Ernährung/Fitness.

Aussage aus dem Video:
"{video_context}"

Externe Evidenz zu diesem Thema:
"{evidence}"

Bewerte die Video-Aussage anhand dieser externen Evidenz."""
        else:
            prompt = f"""Du bist ein wissenschaftlicher Fact-Checker im Bereich Ernährung/Fitness.

Aussage aus dem Video:
"{video_context}"

Keine externe Quelle verfügbar. Bewerte die Aussage anhand deines allgemeinen wissenschaftlichen Wissens."""

        full_prompt = f"""{prompt}

Antworte in genau diesem Format:
BEWERTUNG: [Weitgehend bestätigt / Teilweise bestätigt / Umstritten / Nicht ausreichend belegt]
BEGRÜNDUNG: [2-3 Sätze]"""

        result: FactCheckResult = fact_check_llm.invoke(full_prompt)
        return (
            f"BEWERTUNG: {result.bewertung}\n"
            f"BEGRÜNDUNG: {result.begruendung}\n"
            f"HINWEIS: {evidence_note}"
        )

    return [
        search_video_tool,
        multi_query_search_tool,
        search_by_timestamp_tool,
        summarize_video_tool,
        get_video_metadata_tool,
        fact_check_tool,
    ]