import base64
import logging
import math

from pydoover.processor import Application
from pydoover.models import MessageCreateEvent

from .app_config import Rak4631ProcessorConfig
from .app_tags import Rak4631Tags
from .app_ui import Rak4631UI
from . import decoder

log = logging.getLogger(__name__)


class Rak4631Processor(Application):
    config_cls = Rak4631ProcessorConfig
    ui_cls = Rak4631UI
    tags_cls = Rak4631Tags

    config: Rak4631ProcessorConfig
    tags: Rak4631Tags
    ui: Rak4631UI

    async def on_message_create(self, event: MessageCreateEvent):
        if event.channel.name != "on_tts_event":
            return

        uplink = event.message.data.get("uplink_message")
        if not uplink:
            return

        frm = uplink.get("frm_payload")
        if not frm:
            return

        try:
            payload = base64.b64decode(frm)
        except Exception:
            log.exception("Failed to base64-decode frm_payload: %r", frm)
            return

        decoded = decoder.decode(payload)
        if not decoded:
            log.warning("RAK4631 payload len=%s did not match expected format", len(payload))
            return

        log.info("RAK4631 decoded: %s", decoded)

        litres_per_count = self.config.litres_per_count.value or 0

        await self.tags.raw_current_ma.set(decoded["current_ma"])
        await self.tags.count_reading.set(decoded["count_reading"])
        await self.tags.total_count.set(decoded["total_count"])
        await self.tags.raw_battery_v.set(round(decoded["battery_v"], 2))
        await self.tags.sleep_time_s.set(decoded["sleep_time_s"])
        await self.tags.fast_rate_counter.set(decoded["fast_rate_counter"])
        await self.tags.total_litres.set(round(decoded["total_count"] * litres_per_count, 1))

        # 4-20 mA → cm using the legacy mapping: ((mA - 4) * 0.1875 * 1.6 * 100)
        # Sensor is considered offline when current is below the 4 mA loop threshold.
        raw_cm = None
        if decoded["current_ma"] > 3.8:
            raw_cm = round((decoded["current_ma"] - 4) * 0.1875 * 1.6 * 100, 4)
        await self.tags.raw_current_cm.set(raw_cm)

        level_pct = self._compute_level_pct(raw_cm)
        if level_pct is not None:
            await self.tags.level_pct.set(level_pct)

        battery_pct = round(self._batt_volts_to_percent(decoded["battery_v"]) * 100)
        await self.tags.battery_pct.set(battery_pct)

        flow_rate = None
        if decoded["sleep_time_s"]:
            flow_rate = round(
                (decoded["count_reading"] * litres_per_count) / (decoded["sleep_time_s"] / 60), 2
            )
        await self.tags.flow_rate_lpm.set(flow_rate)

        await self._assess_warnings(level_pct, battery_pct, decoded["fast_rate_counter"])

    def _compute_level_pct(self, raw_cm: float | None) -> float | None:
        if raw_cm is None:
            return None

        zero_cal = self._param("input_zero_cal", 0)
        scaling_cal = self._param("input_scaling_cal", 1)
        sensor_max = self._param("input_max", 250)
        tank_type = self._param("tank_type", "Flat Bottom")

        processed = (raw_cm + zero_cal) * scaling_cal
        if not sensor_max:
            return None
        pct = round((processed / sensor_max) * 100, 1)

        if tank_type == "Horizontal Cylinder":
            r = 50.0
            h = max(0.0, min(pct, 100.0))
            try:
                pct = math.acos((r - h) / r) * (r * r) - (r - h) * math.sqrt(2 * r * h - h * h)
            except ValueError:
                pass

        return pct

    def _param(self, name: str, default):
        try:
            element = getattr(self.ui.details, name, None) or getattr(self.ui, name, None)
            if element is None:
                return default
            value = element.value
            return value if value is not None else default
        except Exception:
            return default

    @staticmethod
    def _batt_volts_to_percent(volts: float | None) -> float:
        if volts is None:
            return 0.0
        if volts < 2.8:
            out = 0.0
        elif volts < 3.1:
            out = (volts - 3.1) * (1 / 3)
        else:
            out = 0.1 + (volts - 3.1) * 1.5
        return max(0.0, min(out, 1.0))

    async def _assess_warnings(self, level_pct, battery_pct, fast_rate_counter):
        level_alarm = self._param("input_low_level", None)
        batt_alarm = self._param("batt_alarm_level", None)

        new_level_warn = (
            level_alarm is not None and level_pct is not None and level_pct < level_alarm
        )
        new_batt_warn = (
            batt_alarm is not None and battery_pct is not None and battery_pct < batt_alarm
        )
        new_high_rate = fast_rate_counter > 0

        prev_level = await self.tags.level_low_warning.get()
        prev_batt = await self.tags.batt_low_warning.get()

        await self.tags.level_low_warning.set(new_level_warn)
        await self.tags.batt_low_warning.set(new_batt_warn)
        await self.tags.high_rate_warning.set(new_high_rate)

        if new_level_warn and not prev_level:
            await self._notify("Level is getting low")
        if new_batt_warn and not prev_batt:
            await self._notify("Battery is getting low")

    async def _notify(self, message: str):
        log.info("RAK4631 notification: %s", message)
        await self.api.create_message("significantEvent", message)
        await self.api.create_message("activity_logs", {"activity_log": {"action_string": message}})
