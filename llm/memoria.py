"""
llm/memoria.py
LLM integration using LangChain + ChatGroq.
Minimal system prompt — context comes from Pinecone retrieval.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        max_tokens=1024,
    )


def call_llm(
    user_message: str,
    context: str,
    profile_names: list,
    history: list,
    has_media: bool = False,
) -> str:
    """
    Calls the LLM with retrieved context.
    Minimal system prompt — intelligence comes from retrieved chunks.
    """
    names_str  = ", ".join(profile_names)
    media_note = (
        "The UI is already displaying the relevant photos to the user. "
        "Do NOT describe, list, or make up any photo descriptions. "
        "Simply acknowledge the photos warmly in one sentence."
    ) if has_media else ""

    if context.strip():
        context_block = f"CONTEXT:\n{context}"
        no_info_rule  = "Answer ONLY from the context above. If the specific detail is not there, say you don't have that information."
    else:
        context_block = "CONTEXT: [No information available]"
        no_info_rule  = "You have no information about this. Tell the user honestly and briefly that you don't have that detail."

    system = SystemMessage(content=f"""You are Memoria. You help users remember their loved ones.
You are answering about: {names_str}.
Be brief and direct. No filler phrases or unnecessary intros.
NEVER make up facts, stories, quotes, or photos. NEVER guess.
{no_info_rule}
{media_note}

{context_block}""")

    messages = [system]

    # Add conversation history
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    llm      = get_llm()
    response = llm.invoke(messages)
    return response.content


def general_chat(user_message: str, history: list) -> str:
    """Handles greetings and general messages with no profile context."""
    system = SystemMessage(content="""You are Memoria on Aeternum, a platform for preserving memories of loved ones.
Rules:
- For greetings, respond warmly in one sentence and invite the user to ask about someone they're connected with.
- If the user is asking about a specific person you have no data on, respond with exactly: "I don't have [name] in your connected profiles."
- NEVER ask follow-up questions. NEVER pretend to search. NEVER make up any information.
- One sentence only.""")

    messages = [system]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    llm      = get_llm()
    response = llm.invoke(messages)
    return response.content
