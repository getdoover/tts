from pathlib import Path

from pydoover import ui

from .app_tags import Rak4631Tags


class Rak4631UI(ui.UI, hidden="$config.app().hide_ui"):
    level = ui.NumericVariable(
        "Level (%)",
        value=Rak4631Tags.level_pct,
        precision=1,
        form="radialGauge",
        ranges=[
            ui.Range("Low", 0, 20, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Half", 20, 70, ui.Colour.blue, show_on_graph=True),
            ui.Range("Full", 70, 100, ui.Colour.green, show_on_graph=True),
        ],
    )

    flow_rate = ui.NumericVariable(
        "Current Flow Rate (L/min)",
        value=Rak4631Tags.flow_rate_lpm,
        precision=1,
    )

    level_low_warning = ui.WarningIndicator(
        "Level Low",
        hidden="!$tag.app().level_low_warning",
    )
    batt_low_warning = ui.WarningIndicator(
        "Battery Low",
        hidden="!$tag.app().batt_low_warning",
    )
    high_rate_warning = ui.WarningIndicator(
        "High-Rate Burst Active",
        hidden="!$tag.app().high_rate_warning",
    )

    details = ui.Submodule(
        "Details",
        children=[
            ui.Select(
                "Tank Type",
                options=[ui.Option("Flat Bottom"), ui.Option("Horizontal Cylinder")],
                name="tank_type",
            ),
            ui.FloatInput("Max Level (cm)", min_val=0, max_val=999, name="input_max"),
            ui.FloatInput("Low level alarm (%)", min_val=0, max_val=99, name="input_low_level"),
            ui.FloatInput("Zero Calibration (cm)", min_val=-999, max_val=999, name="input_zero_cal"),
            ui.FloatInput("Scaling Calibration (x multiply)", min_val=-999, max_val=999, name="input_scaling_cal"),
            ui.FloatInput("Battery Alarm (%)", min_val=0, max_val=100, name="batt_alarm_level"),
            ui.NumericVariable(
                "Battery (%)",
                value=Rak4631Tags.battery_pct,
                precision=0,
                ranges=[
                    ui.Range("Low", 0, 30, ui.Colour.yellow, show_on_graph=True),
                    ui.Range("Half", 30, 80, ui.Colour.blue, show_on_graph=True),
                    ui.Range("Full", 80, 100, ui.Colour.green, show_on_graph=True),
                ],
            ),
            ui.NumericVariable(
                "Total Litres (L)", value=Rak4631Tags.total_litres, precision=1, name="total_litres"
            ),
            ui.NumericVariable(
                "Raw Level Reading (mA)", value=Rak4631Tags.raw_current_ma, precision=2, name="raw_current_ma"
            ),
            ui.NumericVariable(
                "Raw Level Reading (cm)", value=Rak4631Tags.raw_current_cm, precision=1, name="raw_current_cm"
            ),
            ui.NumericVariable(
                "Last Raw Count", value=Rak4631Tags.count_reading, precision=0, name="count_reading"
            ),
            ui.NumericVariable(
                "Raw Count Total", value=Rak4631Tags.total_count, precision=0, name="total_count"
            ),
            ui.NumericVariable(
                "Battery (V)", value=Rak4631Tags.raw_battery_v, precision=2, name="raw_battery_v"
            ),
        ],
    )


def export():
    Rak4631UI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "rak4631_processor",
    )
