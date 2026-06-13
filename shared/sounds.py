"""
shared/sounds.py — chimes suaves generados en runtime (sin assets binarios).

Genera WAVs cortos una sola vez en el tempdir y los reproduce async en Windows
vía winsound. No-op fuera de Windows o si la generación/reproducción falla
(nunca lanza). Mismo enfoque que el chime del Temporizador, centralizado para
reutilizarlo (p. ej. el sonido de logro de la Checklist de Rutina Diaria).
"""

from __future__ import annotations

import logging
import math
import os
import struct
import sys
import tempfile
import wave

_log = logging.getLogger(__name__)

_ACHIEVEMENT_PATH = os.path.join(tempfile.gettempdir(), "nm_achievement.wav")


def _ensure_wav(path: str, notes: list[tuple[float, float]]) -> str | None:
    """Genera (una sola vez) un WAV corto y cálido con la secuencia de notas."""
    try:
        if os.path.exists(path) and os.path.getsize(path) > 1024:
            return path
    except Exception:
        pass
    try:
        sample_rate = 22050
        attack = 0.03
        release = 0.10
        frames = bytearray()
        for freq, dur in notes:
            n_samples = int(sample_rate * dur)
            for i in range(n_samples):
                t = i / sample_rate
                if t < attack:
                    env = t / attack
                elif t > dur - release:
                    env = max(0.0, (dur - t) / release)
                else:
                    env = 1.0
                sample = (
                    0.6 * math.sin(2 * math.pi * freq * t)
                    + 0.15 * math.sin(2 * math.pi * freq * 2 * t)
                )
                frames.extend(struct.pack("<h", int(sample * env * 0.5 * 32767)))
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(bytes(frames))
        return path
    except Exception:
        _log.debug("No se pudo generar el WAV de chime (%s)", path)
        return None


def _play(path: str | None) -> None:
    try:
        if sys.platform != "win32" or not path:
            return
        import winsound

        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        _log.debug("No se pudo reproducir el chime")


def play_achievement() -> None:
    """Sonido de logro al completar un ítem (Checklist de Rutina Diaria).

    Arpegio ascendente breve y brillante (~0.5s): C5 → E5 → G5. Distinto de la
    alarma del Temporizador (más grave y larga) para que se lea como "logro".
    """
    path = _ensure_wav(
        _ACHIEVEMENT_PATH,
        [(523.25, 0.13), (659.25, 0.13), (783.99, 0.22)],
    )
    _play(path)
