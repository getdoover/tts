from pathlib import Path

from pydoover import config
from pydoover.processor import IngestionEndpointConfig, ExtendedPermissionsConfig


class TtsIntegrationConfig(config.Schema):
    permissions = ExtendedPermissionsConfig()

    tts_api_key = config.String(
        "TTS API Key",
        description="Bearer token for The Things Stack API",
    )
    tts_app_name = config.String(
        "TTS Application Name",
        description="Application ID in The Things Stack console",
    )
    tts_server_host = config.String(
        "TTS Server Host",
        description="TTS cluster hostname (e.g. au1.cloud.thethings.network)",
        default="au1.cloud.thethings.network",
    )

    integration = IngestionEndpointConfig()


def export():
    TtsIntegrationConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "tts_integration",
    )
