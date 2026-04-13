from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig


class Rak4631ProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_tts_event"], hidden=True)
    position = config.ApplicationPosition()

    litres_per_count = config.Number(
        "Litres per Count",
        description="How many litres each pulse from the flow meter represents.",
        default=10.0,
    )

    hide_ui = config.Boolean(
        "Hide Default UI",
        description="Whether to hide the default UI. Useful if you have a custom UI application.",
        default=False,
    )


def export():
    Rak4631ProcessorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "rak4631_processor",
    )
