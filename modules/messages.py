# ui_messages.py

import streamlit as st
from typing import List, Dict, Any
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions

logger = setup_logging(__file__)

@logs_and_exceptions(logger)
def ui_messages(messages: List[Dict[str, Any]]) -> None:
    """Display chat messages in the Streamlit UI."""
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])