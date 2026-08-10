from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from config import llm
from tools import all_tools

checkpointer = MemorySaver()
agent = create_agent(llm, all_tools, checkpointer=checkpointer)


def ask_agent(question: str, thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    return response["messages"][-1].content