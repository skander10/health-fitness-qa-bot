from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from config import llm
from tools import all_tools
from tools import all_tools, clean_fact_check_format
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3


#checkpointer = MemorySaver()
conn = sqlite3.connect("../data/checkpoints.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(conn)

SYSTEM_PROMPT = """Du bist ein hilfreicher Assistent für Fragen zu einem YouTube-Video über Ernährung und Gehirngesundheit.

WICHTIGE REGEL: Wenn du das fact_check_tool nutzt, gib dessen Ergebnis EXAKT UND UNVERÄNDERT weiter, 
ohne es umzuformulieren, zusammenzufassen oder in eigene Worte zu fassen. Das Format 
(BEWERTUNG:/BEGRÜNDUNG:/HINWEIS:) muss in deiner finalen Antwort exakt erhalten bleiben."""

agent = create_agent(llm, all_tools, checkpointer=checkpointer, system_prompt=SYSTEM_PROMPT)


def ask_agent(question: str, thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    return clean_fact_check_format(response["messages"][-1].content)


def ask_agent_with_trace(question: str, thread_id: str) -> dict:
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