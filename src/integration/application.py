import logging

from pydoover.processor import Application
from pydoover.models import IngestionEndpointEvent

from .app_config import TtsIntegrationConfig

log = logging.getLogger(__name__)


class TtsIntegration(Application):
    config: TtsIntegrationConfig
    config_cls = TtsIntegrationConfig

    async def setup(self):
        log.info("TTS LoRaWAN integration initialized")

    async def on_ingestion_endpoint(self, event: IngestionEndpointEvent):
        """
        Handle incoming webhook from The Things Stack.

        TTS sends JSON payloads containing end_device_ids and one of:
        uplink_message, join_accept, downlink_ack/nack/sent/failed/queued.
        We extract the device_id and forward the payload to the correct device agent.
        """
        payload = event.payload
        if payload is None:
            log.warning("Received empty TTS payload")
            return

        # Extract device identifier from TTS payload
        end_device_ids = payload.get("end_device_ids", {})
        device_id = end_device_ids.get("device_id")

        if not device_id:
            log.warning("No device_id in TTS payload")
            return

        log.info(f"Received TTS event for device: {device_id}")

        # Look up the Doover agent for this TTS device
        try:
            device_mapping = self.tag_manager.get_tag(
                "serial_number_lookup",
                app_key="tts_processor_1",
                raise_key_error=True,
            )
        except KeyError:
            log.info(
                f"Device mapping not found. Tags: {self.tag_manager._tag_values}. Skipping..."
            )
            return

        agent_id = device_mapping.get(device_id)

        log.info(
            f"Device: {device_id}, Agent ID: {agent_id}, Mapping: {device_mapping}"
        )

        # Store the event on this integration's agent
        await self.api.create_message("tts_events", payload)

        # Forward to the device agent if we have a mapping
        if agent_id:
            log.info(f"Forwarding to agent {agent_id}")
            await self.api.create_message("on_tts_event", payload, agent_id=agent_id)
