import tiktoken
import streamlit as st
from typing import List, Dict, Any
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions

logger = setup_logging(__file__)

@logs_and_exceptions(logger)
def num_tokens_from_messages(messages: List[Dict[str, Any]], model: str = "gpt-4") -> int:
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning(f"Model {model} not found. Using cl100k_base encoding.")
        st.warning(f"Warning: model {model} not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens_per_message = 3
    tokens_per_name = 1

    def count_tokens(obj: Any) -> int:
        if isinstance(obj, str):
            return len(encoding.encode(obj))
        elif isinstance(obj, dict):
            return sum(count_tokens(key) + count_tokens(value) for key, value in obj.items())
        elif isinstance(obj, list):
            return sum(count_tokens(item) for item in obj)
        else:
            return 0  # For other types (int, float, bool, etc.), we don't count tokens

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += count_tokens(key)
            num_tokens += count_tokens(value)
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3  # every reply is primed with assistant
    return num_tokens