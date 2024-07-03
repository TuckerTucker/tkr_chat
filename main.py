# main.py
import argparse
from typing import Dict, List, Any

import streamlit as st

from tkr_utils.app_paths import AppPaths
from tkr_utils.helper_openai import OpenAIHelper
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions

from modules.token_counter import num_tokens_from_messages
from modules.file_io import load_default_chat, load_chat_history_from_file, update_chat_history_to_file
from modules.messages import ui_messages

# Setup logging
logger = setup_logging(__file__)

# Initialize AppPaths
AppPaths.check_directories()

# Initialize OpenAI helper
openai_helper = OpenAIHelper()

@logs_and_exceptions(logger)
def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Load chat history.")
    parser.add_argument("--load_chat", type=str, help="File to load chat history from.")
    return parser.parse_args()

@logs_and_exceptions(logger)
def load_default_to_session_state() -> None:
    """Load default conversation to session state."""
    default_conversation = load_default_chat()
    st.session_state.messages = default_conversation["messages"]
    st.session_state.prompts = default_conversation["prompts"]
    st.session_state.filename = default_conversation["filename"]
    st.session_state.ai_settings = default_conversation["ai_settings"]
    logger.info("Loaded default conversation to session state")

@logs_and_exceptions(logger)
def handle_user_input(prompt: str) -> None:
    """
    Process user input and generate AI response.

    Args:
        prompt (str): User input prompt.
    """
    max_tokens = st.session_state.ai_settings["max_tokens"]
    st.session_state.messages.append({"role": "user", "content": prompt})
    ui_messages([{"role": "user", "content": prompt}])

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

    # Calculate tokens and prepare messages for OpenAI
    tokens_so_far = 0
    last_index = 0
    for i, message in enumerate(reversed(st.session_state.messages)):
        tokens = num_tokens_from_messages([message], model=st.session_state.ai_settings["model"])
        if tokens_so_far + tokens > max_tokens:
            break
        tokens_so_far += tokens
        last_index = len(st.session_state.messages) - i - 1

    model = st.session_state.ai_settings["model"]
    
    if last_index > 0:
        skipped = last_index
        st.session_state.long_convo_msg = f"> ✂️&nbsp;&nbsp;The first **{skipped}** messages are no longer seen by the AI. The chat has grown beyond the context window for this model ({model} — {max_tokens} tokens)."
    else:
        st.session_state.long_convo_msg = None

    oai_messages = [
        {"role": "system", "content": st.session_state.prompts.get("system_prompt")},
        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[last_index:]]
    ]

    # Generate AI response
    full_response = ""
    try:
        stream = openai_helper.client.chat.completions.create(
            model=openai_helper.model,
            messages=oai_messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                message_placeholder.markdown(full_response + "▌")

            if chunk.choices[0].finish_reason:
                if chunk.choices[0].finish_reason == 'length':
                    st.warning("The response was cut-off due to length.")
                break

        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Update chat history
        update_chat_history_to_file(st.session_state.filename, st.session_state.messages)
        logger.info("Updated chat history file")
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        st.error("An error occurred while generating the AI response. Please try again.")

@logs_and_exceptions(logger)
def main() -> None:
    """Main function to run the Streamlit app."""
    args = parse_arguments()

    if not all(key in st.session_state for key in ["messages", "prompts", "filename"]):
        if args.load_chat:
            try:
                st.session_state.messages, st.session_state.prompts, st.session_state.ai_settings = load_chat_history_from_file(args.load_chat)
                st.session_state.filename = args.load_chat
                logger.info(f"Loaded chat history from {args.load_chat}")
            except FileNotFoundError:
                st.warning(f"Could not find file {args.load_chat}. Initializing with default message.")
                load_default_to_session_state()
        else:
            load_default_to_session_state()

    ui_messages(st.session_state.messages)

    if prompt := st.chat_input(st.session_state.prompts.get("default_prompt")):
        handle_user_input(prompt)

    if "long_convo_msg" in st.session_state and st.session_state.long_convo_msg is not None:
        st.markdown(st.session_state.long_convo_msg)
        st.session_state.long_convo_msg = None

if __name__ == "__main__":
    main()