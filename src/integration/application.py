import base64
import logging
from dataclasses import dataclass
from typing import Any

import httpx
from pydoover.processor import Application
from pydoover.models import IngestionEndpointEvent, MessageCreateEvent

from .app_config import TtsIntegrationConfig

log = logging.getLogger(__name__)

# Channel the processor writes to when it wants to send a downlink. The
# integration subscribes to this channel on every mapped device via its
# egress config.
DOWNLINK_REQUEST_CHANNEL = "tts_downlink_request"
UPLINK_CHANNEL = "on_tts_event"


@dataclass(frozen=True, slots=True)
class DownlinkRequest:
    device_id: str
    f_port: int
    payload: Any
    confirmed: bool = False
    priority: str = "NORMAL"


class TtsIntegration(Application):
    config: TtsIntegrationConfig
    config_cls = TtsIntegrationConfig

    # -- Uplink path ---------------------------------------------------------

    async def on_ingestion_endpoint(self, event: IngestionEndpointEvent):
        """
        Handle incoming webhook from The Things Stack.

        TTS sends JSON payloads containing end_device_ids and one of:
        uplink_message, join_accept, downlink_ack/nack/sent/failed/queued.
        We extract the device_id and forward the payload to the correct
        device agent.
        """
        payload = event.payload
        if payload is None:
            log.warning("Received empty TTS payload")
            return

        end_device_ids = payload.get("end_device_ids", {})
        device_id = end_device_ids.get("device_id")
        if not device_id:
            log.warning("No device_id in TTS payload")
            return

        log.info("TTS uplink for device: %s", device_id)

        agent_id = self._lookup_agent(device_id)

        await self.api.create_message("tts_events", payload)

        if agent_id is None:
            log.info("No agent mapped to device %s — event stored only", device_id)
            return

        await self.api.create_message(UPLINK_CHANNEL, payload, agent_id=agent_id)

    # -- Downlink path -------------------------------------------------------

    async def on_message_create(self, event: MessageCreateEvent):
        """
        Handle a downlink-publish request.

        Devices publish to the `tts_downlink_request` channel on their own
        agent; the integration is subscribed to that channel via its egress
        config. The source agent_id is reverse-mapped to a TTS device_id
        via `serial_number_lookup`, unless `device_id` is set explicitly
        on the payload.
        """
        if event.channel.name != DOWNLINK_REQUEST_CHANNEL:
            return

        data = event.message.data
        device_id = data.get("device_id")
        if not device_id:
            device_id = self._lookup_device_id(event.channel.agent_id)
        if not device_id:
            log.warning(
                "Downlink from agent %s has no device_id mapping — dropping",
                event.channel.agent_id,
            )
            return

        await self._publish_downlink(DownlinkRequest(
            device_id=device_id,
            f_port=data.get("f_port", 1),
            payload=data.get("payload"),
            confirmed=data.get("confirmed", False),
            priority=data.get("priority", "NORMAL"),
        ))

    # -- Helpers -------------------------------------------------------------

    def _lookup_agent(self, device_id: str) -> int | None:
        mapping = self._serial_number_lookup()
        if mapping is None:
            return None
        return mapping.get(device_id)

    def _lookup_device_id(self, agent_id: int) -> str | None:
        mapping = self._serial_number_lookup()
        if mapping is None:
            return None
        for device_id, mapped_agent_id in mapping.items():
            if str(mapped_agent_id) == str(agent_id):
                return device_id
        return None

    def _serial_number_lookup(self) -> dict | None:
        try:
            return self.tag_manager.get_tag(
                "serial_number_lookup",
                app_key="tts_processor_1",
                raise_key_error=True,
            )
        except KeyError:
            log.debug("serial_number_lookup tag missing; processor not yet installed?")
            return None

    async def _publish_downlink(self, request: DownlinkRequest) -> None:
        server = self.config.tts_server_host.value
        app_id = self.config.tts_app_name.value
        api_key = self.config.tts_api_key.value

        if not (server and app_id and api_key):
            log.error("TTS integration is missing server/app/api_key — cannot publish downlink")
            return

        downlink: dict[str, Any] = {
            "f_port": request.f_port,
            "priority": request.priority,
            "confirmed": request.confirmed,
        }
        payload = request.payload
        if isinstance(payload, dict):
            downlink["decoded_payload"] = payload
        elif isinstance(payload, (bytes, bytearray)):
            downlink["frm_payload"] = base64.b64encode(bytes(payload)).decode()
        elif isinstance(payload, str):
            # Treat strings as hex-encoded raw frames (matches common
            # downlink tooling). If users need raw ASCII, they can wrap
            # it in `decoded_payload` on the sending side.
            try:
                raw = bytes.fromhex(payload)
            except ValueError:
                log.error("Downlink payload string is not valid hex: %r", payload)
                return
            downlink["frm_payload"] = base64.b64encode(raw).decode()
        elif payload is None:
            downlink["frm_payload"] = ""
        else:
            log.error("Unsupported downlink payload type: %s", type(payload).__name__)
            return

        url = (
            f"https://{server}/api/v3/as/applications/{app_id}"
            f"/devices/{request.device_id}/down/push"
        )
        body = {"downlinks": [downlink]}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.HTTPError as e:
            log.error("Downlink push to device %s failed: %s", request.device_id, e)
            return

        if resp.status_code >= 300:
            log.error(
                "Downlink push to device %s failed %s: %s",
                request.device_id, resp.status_code, resp.text,
            )
        else:
            log.info("Pushed downlink to device %s (f_port=%s)", request.device_id, request.f_port)
