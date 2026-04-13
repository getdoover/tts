import logging
from datetime import datetime, timezone, timedelta

from pydoover.processor import Application
from pydoover.models import MessageCreateEvent, ConnectionStatus

from .app_config import TtsProcessorConfig
from .app_tags import TtsTags
from .app_ui import TtsUI

log = logging.getLogger(__name__)


class TtsProcessor(Application):
    config_cls = TtsProcessorConfig
    ui_cls = TtsUI
    tags_cls = TtsTags

    config: TtsProcessorConfig
    tags: TtsTags
    ui: TtsUI

    async def on_message_create(self, event: MessageCreateEvent):
        """
        Handle incoming TTS events forwarded from the integration.

        The integration receives TTS webhooks and forwards the full
        payload to the `on_tts_event` channel on each device agent.
        """
        if event.channel.name != "on_tts_event":
            return

        data = event.message.data
        log.info(f"Processing TTS event: {data}")

        # Route by message type
        if "uplink_message" in data:
            await self.handle_uplink(data)
        elif "join_accept" in data:
            log.info("Device joined the network")
        elif any(k in data for k in
                 ("downlink_sent", "downlink_failed", "downlink_queued", "downlink_ack", "downlink_nack")):
            log.info(f"Downlink event received")

        # Update connection status
        await self.ping_connection(
            online_at=datetime.now(timezone.utc),
            connection_status=ConnectionStatus.periodic_unknown,
            offline_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

    async def handle_uplink(self, data: dict):
        """Process a TTS uplink message and update tags."""
        uplink = data["uplink_message"]

        # Frame counter
        if "f_cnt" in uplink:
            await self.tags.frame_counter.set(uplink["f_cnt"])

        # Radio metadata from the best gateway (by RSSI)
        rx_metadata = uplink.get("rx_metadata", [])
        if rx_metadata:
            best = max(rx_metadata, key=lambda r: r.get("rssi", -999))
            await self.tags.rssi.set(best.get("rssi"))
            await self.tags.snr.set(best.get("snr"))
            await self.tags.gateway.set(best.get("gateway_ids", {}).get("gateway_id"))

        # Frequency and data rate from settings
        settings = uplink.get("settings", {})
        freq = settings.get("frequency")
        if freq:
            await self.tags.frequency.set(f"{int(freq) / 1_000_000:.1f} MHz")

        data_rate = settings.get("data_rate", {}).get("lora", {})
        sf = data_rate.get("spreading_factor")
        bw = data_rate.get("bandwidth")
        if sf and bw:
            await self.tags.data_rate.set(f"SF{sf}BW{bw // 1000}")

        # Decoded payload (if TTS has a payload formatter configured)
        decoded = uplink.get("decoded_payload")
        if decoded:
            await self.tags.decoded_payload.set(decoded)
