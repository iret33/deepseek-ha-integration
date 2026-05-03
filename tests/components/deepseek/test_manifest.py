"""Smoke tests for the DeepSeek integration."""

from __future__ import annotations

import json
from pathlib import Path


def test_manifest_valid() -> None:
    """Integration manifest is valid and well-formed."""
    manifest_path = (
        Path(__file__).resolve().parents[3]
        / "custom_components"
        / "deepseek"
        / "manifest.json"
    )
    data = json.loads(manifest_path.read_text())

    assert data["domain"] == "deepseek"
    assert data["name"]
    assert data["codeowners"]
    assert data["config_flow"] is True
    assert "conversation" in data["dependencies"]
    assert data["integration_type"]
    assert data["iot_class"]
    assert data["requirements"]
    assert data["version"]


def test_hacs_json_valid() -> None:
    """HACS manifest is valid."""
    hacs_path = Path(__file__).resolve().parents[3] / "hacs.json"
    data = json.loads(hacs_path.read_text())
    assert data["name"]
    assert "homeassistant" in data


def test_module_imports() -> None:
    """The integration modules can be imported cleanly."""
    import custom_components.deepseek as deepseek_pkg
    from custom_components.deepseek import config_flow, const, conversation

    assert const.DOMAIN == "deepseek"
    assert const.RECOMMENDED_CHAT_MODEL in const.MODELS
    assert hasattr(deepseek_pkg, "async_setup_entry")
    assert hasattr(deepseek_pkg, "async_unload_entry")
    assert hasattr(conversation, "async_setup_entry")
    assert hasattr(conversation, "DeepSeekConversationEntity")
    assert hasattr(config_flow, "ConfigFlow")
