import asyncio
from collections.abc import AsyncIterable
import io
import logging
import wave

import requests

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import MODEL, SUPPORTED_LANGUAGES, TEMPERATURE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up speech-to-text platform via config entry."""
    _LOGGER.debug("Setting up groq_whisper with entry_id=%s", config_entry.entry_id)
    async_add_entities(
        [GroqWhisperSTTEntity(**config_entry.data, unique_id=config_entry.entry_id)]
    )


class GroqWhisperSTTEntity(SpeechToTextEntity):
    """Handle the Groq Whisper STT integration."""

    def __init__(self, host: str, api_key: str, unique_id: str) -> None:
        self.host = host
        self.api_key = api_key
        self.unique_id = unique_id

    @property
    def supported_languages(self) -> list[str]:
        return SUPPORTED_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        return [
            AudioBitRates.BITRATE_8,
            AudioBitRates.BITRATE_16,
            AudioBitRates.BITRATE_24,
            AudioBitRates.BITRATE_32,
        ]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        return [
            AudioSampleRates.SAMPLERATE_8000,
            AudioSampleRates.SAMPLERATE_16000,
            AudioSampleRates.SAMPLERATE_44100,
            AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        return [AudioChannels.CHANNEL_MONO, AudioChannels.CHANNEL_STEREO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        _LOGGER.debug("Processing %s", metadata)

        # Convert the stream to bytes
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk
            if len(audio_data) > 1024 * 1024:
                return SpeechResult("", SpeechResultState.ERROR)

        if not audio_data:
            return SpeechResult("", SpeechResultState.ERROR)

        _LOGGER.debug("Audio data length: %d", len(audio_data))

        try:
            file = io.BytesIO()
            with wave.open(file, "wb") as wav:
                wav.setnchannels(metadata.channel)
                wav.setframerate(metadata.sample_rate)
                wav.setsampwidth(2)
                wav.writeframes(audio_data)

            # Ensure the buffer is at the start before passing it
            file.seek(0)
            files = {
                "file": (
                    "audio.wav",
                    file,
                    "audio/wav",
                )
            }

            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"{self.host}/openai/v1/audio/transcriptions"
            params = {
                "model": MODEL,
                "language": metadata.language,
                "temperature": TEMPERATURE,
                "response_format": "json",
            }

            response = await asyncio.to_thread(
                requests.post,
                url=url,
                headers=headers,
                data=params,
                files=files,
            )

            text = response.json().get("text", "")

            _LOGGER.debug("Text: %s", text)

            if not text:
                _LOGGER.error("No text found in response")
                _LOGGER.error("Response: %s", response.json())
                return SpeechResult("", SpeechResultState.ERROR)

            return SpeechResult(text, SpeechResultState.SUCCESS)

        except requests.exceptions.RequestException as e:
            _LOGGER.error(e)
            return SpeechResult("", SpeechResultState.ERROR)
