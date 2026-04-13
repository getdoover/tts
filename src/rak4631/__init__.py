from typing import Any

from pydoover.processor import run_app

from .application import Rak4631Processor


def handler(event: dict[str, Any], context):
    """Lambda handler entry point."""
    run_app(
        Rak4631Processor(),
        event,
        context,
    )
