from pathlib import Path

from pydoover import ui

from .app_tags import TtsTags


class TtsUI(ui.UI, hidden="$config.app().hide_ui"):
    rssi = ui.NumericVariable(
        "RSSI",
        value=TtsTags.rssi,
        units="dBm",
        precision=0,
        ranges=[
            ui.Range("Weak", -130, -100, ui.Colour.red, show_on_graph=True),
            ui.Range("Fair", -100, -80, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Good", -80, -50, ui.Colour.green, show_on_graph=True),
            ui.Range("Strong", -50, 0, ui.Colour.blue, show_on_graph=True),
        ],
    )

    snr = ui.NumericVariable(
        "SNR",
        value=TtsTags.snr,
        units="dB",
        precision=1,
        ranges=[
            ui.Range("Poor", -20, -5, ui.Colour.red, show_on_graph=True),
            ui.Range("Fair", -5, 5, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Good", 5, 15, ui.Colour.green, show_on_graph=True),
        ],
    )

    frame_counter = ui.NumericVariable(
        "Frame Counter",
        value=TtsTags.frame_counter,
        precision=0,
    )

    frequency = ui.TextVariable(
        "Frequency",
        value=TtsTags.frequency,
    )

    data_rate = ui.TextVariable(
        "Data Rate",
        value=TtsTags.data_rate,
    )


def export():
    TtsUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "tts_processor",
    )
