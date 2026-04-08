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
    """The integration module can be imported cleanly."""
    from custom_components.deepseek import const

    assert const.DOMAIN == "deepseek"
    assert const.DEFAULT_MODEL in const.MODELS
