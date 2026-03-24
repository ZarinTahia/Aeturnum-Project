"""
app.py
Memoria — Streamlit chat UI powered by LangGraph.
"""

import streamlit as st
from graph.workflow import memoria_graph

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(page_title="Memoria", page_icon="🕯️", layout="centered")

LOGGED_IN_USER_ID = "user-001"

st.title("🕯️ Memoria")
st.caption("Ask about the people you're connected with on Aeternum.")
st.divider()

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "resolved_profiles" not in st.session_state:
    st.session_state.resolved_profiles = []

# ─────────────────────────────────────────────
# Render chat history
# ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("media"):
            for item in msg["media"]:
                if item["chunk_type"] == "image":
                    st.image(
                        item["media_url"],
                        caption=f"{item['caption']} · {item['node_title']} ({item['node_date']})",
                        use_container_width=True,
                    )

# ─────────────────────────────────────────────
# Chat input
# ─────────────────────────────────────────────
user_input = st.chat_input("Say something...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Memoria is thinking..."):

            # Build initial LangGraph state
            initial_state = {
                "user_id":          LOGGED_IN_USER_ID,
                "user_message":     user_input,
                "messages":         st.session_state.messages[:-1],
                "resolved_profiles": st.session_state.resolved_profiles,
                "allowed_profiles": [],
                "denied_messages":  [],
                "retrieved_context": "",
                "media_items":      [],
                "wants_media":      False,
                "response":         "",
            }

            # Run the LangGraph workflow
            result = memoria_graph.invoke(initial_state)

            response   = result["response"]
            media_items = result["media_items"]

            # Persist resolved profiles for follow-up messages
            if result["resolved_profiles"]:
                st.session_state.resolved_profiles = result["resolved_profiles"]

        st.markdown(response)

        # Render media inline
        if media_items:
            for item in media_items:
                if item["chunk_type"] == "image" and item["media_url"]:
                    st.image(
                        item["media_url"],
                        caption=f"{item['caption']} · {item['node_title']} ({item['node_date']})",
                        use_container_width=True,
                    )

    st.session_state.messages.append({
        "role":    "assistant",
        "content": response,
        "media":   media_items,
    })
