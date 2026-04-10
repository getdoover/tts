"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from tts.application import TtsApplication
    assert TtsApplication
    assert TtsApplication.config_cls is not None
    assert TtsApplication.tags_cls is not None
    assert TtsApplication.ui_cls is not None

def test_config():
    from tts.app_config import TtsConfig
    schema = TtsConfig.to_schema()
    assert isinstance(schema, dict)
    assert len(schema["properties"]) > 0

def test_tags():
    from tts.app_tags import SampleTags
    assert SampleTags

def test_ui():
    from tts.app_ui import TtsUI
    assert TtsUI

def test_state():
    from tts.app_state import TtsState
    assert TtsState
