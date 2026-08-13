from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from config import llm
from tools import make_tools, clean_fact_check_format

conn = sqlite3.connect("../data/checkpoints.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(conn)

SYSTEM_PROMPT = """Du bist ein hilfreicher Assistent für Fragen zu YouTube-Videos.

WICHTIGE REGEL: Wenn du das fact_check_tool nutzt, gib dessen Ergebnis EXAKT UND UNVERÄNDERT weiter, 
ohne es umzuformulieren, zusammenzufassen oder in eigene Worte zu fassen. Das Format 
(BEWERTUNG:/BEGRÜNDUNG:/HINWEIS:) muss in deiner finalen Antwort exakt erhalten bleiben."""

# Cache: baut den Agent nur einmal pro (topic, video_id)-Kombination, nicht bei jeder Anfrage neu
_agent_cache = {}

def get_agent(topic: str = None, video_id: str = None):
    key = (topic, video_id)
    if key not in _agent_cache:
        tools = make_tools(topic=topic, video_id=video_id)
        _agent_cache[key] = create_agent(llm, tools, checkpointer=checkpointer, system_prompt=SYSTEM_PROMPT)
    return _agent_cache[key]


def ask_agent(question: str, thread_id: str, topic: str = None, video_id: str = None) -> str:
    agent = get_agent(topic=topic, video_id=video_id)
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    return clean_fact_check_format(response["messages"][-1].content)


def ask_agent_with_trace(question: str, thread_id: str, topic: str = None, video_id: str = None) -> dict:
    agent = get_agent(topic=topic, video_id=video_id)
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    messages = response["messages"]

    tools_used = []
    tool_context_parts = []
    for msg in messages:
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])
        if msg.__class__.__name__ == "ToolMessage":
            tool_context_parts.append(str(msg.content))

    return {
        "answer": clean_fact_check_format(messages[-1].content),
        "tools_used": tools_used,
        "context": "\n".join(tool_context_parts),
    }