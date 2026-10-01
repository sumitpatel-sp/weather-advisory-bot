import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from backend.graph import run_agent


st.set_page_config(
    page_title="Weather Advisory Support Bot",
    page_icon="🌤️",
    layout="centered",
)

st.title("🌤️ Weather Advisory Support Bot")
st.caption("Recommendations use live Open-Meteo data and written safety SOPs.")


def show_assistant_response(response):
    if response.startswith("Recommendation (SOP-"):
        recommendation, weather_part = response.split(
            "\n\nWhy this SOP applies:",
            1,
        )

        title, advice = recommendation.split(": ", 1)

        st.markdown(f"#### {title}")
        st.success(advice)

        st.markdown("**Live weather checked**")
        st.caption(weather_part.strip())

    elif response.startswith("I found no written"):
        st.warning(response)

    elif response.startswith("I could not"):
        st.error(response)

    else:
        st.markdown(response)


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            show_assistant_response(message["content"])
        else:
            st.markdown(message["content"])


user_input = st.chat_input(
    "Example: Can I go for picnic today in Mumbai?"
)

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Checking live weather and written SOPs..."):
            try:
                response = run_agent(
                    user_input,
                    st.session_state.messages,
                )
            except Exception:
                response = (
                    "I could not complete this request right now. "
                    "Please try again shortly."
                )

        show_assistant_response(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )