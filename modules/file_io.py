# file_io.py

import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
from tkr_utils.app_paths import AppPaths
from tkr_utils.config_logging import setup_logging
from tkr_utils.decorators import logs_and_exceptions
from pathlib import Path
logger = setup_logging(__file__)

@logs_and_exceptions(logger)
def load_chat_history_from_file(filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    """Load chat history and prompts from a file."""
    filepath = AppPaths.CHAT_LOGS / filename
    with open(filepath, "r") as f:
        data = json.loads(f.read())
        return data["conversation"], data["prompts"], data["ai_settings"]

@logs_and_exceptions(logger)
def update_chat_history_to_file(filename: str, messages: List[Dict[str, Any]]) -> None:
    """Update chat history in a file."""
    filepath =  AppPaths.CHAT_LOGS / filename
    with open(filepath, "r") as f:
        data = json.loads(f.read())
    
    for message in messages:
        message["date"] = datetime.now().strftime("%Y-%m-%d")
        message["time"] = datetime.now().strftime("%H:%M:%S.%f")
    data["conversation"] = messages
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

@logs_and_exceptions(logger)
def load_default_chat() -> Dict[str, Any]:
    """Load default conversation template and create a new chat file."""
    default_template_path = Path("modules/convo_default")
    with open(default_template_path, "r") as f:
        data = json.loads(f.read())
    
    timestamp = datetime.now().strftime("%b%d_%I_%M_%S%p").lower()
    new_filename = f"convo_{timestamp}"
    new_filepath = AppPaths.CHAT_LOGS / new_filename

    with open(new_filepath, "w") as f:
        json.dump(data, f, indent=2)

    return {
        "messages": data["conversation"],
        "prompts": data["prompts"],
        "filename": new_filename,
        "ai_settings": data["ai_settings"]
    }