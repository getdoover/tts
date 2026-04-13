from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig, SerialNumberConfig


class TtsProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_tts_event"], hidden=True)
    position = config.ApplicationPosition()
    # this should be populated by the integration (there's some funny business on auto-fetching/creating device id from tts)
    # serial_number = SerialNumberConfig(
    #     # description="TTS Device Name (e.g. eui-70b3-d57e-d004-8ea5)",
    #     hidden=True,
    #     default="",
    # )

    hide_ui = config.Boolean(
        "Hide Default UI",
        description="Whether to hide the default UI. Useful if you have a custom UI application.",
        default=False,
    )


def export():
    TtsProcessorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "tts_processor",
    )
