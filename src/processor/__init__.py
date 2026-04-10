from typing import Any

from pydoover.processor import run_app

from .application import TtsProcessor


def handler(event: dict[str, Any], context):
    """Lambda handler entry point."""
    run_app(
        TtsProcessor(),
        event,
        context,
    )
