"""The groq_whisper integration."""

from __future__ import annotations

from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_PLATFORMS: list[Platform] = [Platform.STT]


class GroqWhisperData(TypedDict):
    """Data for the groq_whisper integration."""

    host: str
    api_key: str


type GroqWhisperConfigEntry = ConfigEntry[GroqWhisperData]


async def async_setup_entry(hass: HomeAssistant, entry: GroqWhisperConfigEntry) -> bool:
    """Set up groq_whisper from a config entry."""

    hass.states.async_set("groq_whisper.initialized", "True")

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GroqWhisperConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
