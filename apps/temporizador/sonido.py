"""sonido.py — Alarma terapéutica suave para el Temporizador de Actividades."""
import math
import threading

try:
    import numpy as np
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    _DISPONIBLE = True
except Exception:
    _DISPONIBLE = False

DISPONIBLE = _DISPONIBLE
TIPOS = {
    "campana":    "Campana tibetana",
    "progresiva": "Campana progresiva (fade-in)",
    "silencio":   "Solo destello visual",
}


def _generar_campana(sr: int = 44100, dur: float = 2.6, vol: float = 1.0) -> "np.ndarray":
    """Sintetiza una campana tibetana con armónicos inarmónicos reales."""
    t = np.linspace(0, dur, int(sr * dur), False)
    f0 = 432.0
    # Armónicos aproximados de un cuenco tibetano real
    onda = (
        np.sin(2 * math.pi * f0 * t)         * np.exp(-t * 1.1)  * 0.55 +
        np.sin(2 * math.pi * f0 * 2.76 * t)  * np.exp(-t * 2.0)  * 0.27 +
        np.sin(2 * math.pi * f0 * 5.40 * t)  * np.exp(-t * 3.5)  * 0.12 +
        np.sin(2 * math.pi * f0 * 8.93 * t)  * np.exp(-t * 5.5)  * 0.06
    )
    # Fade-in de 40 ms para evitar clic de ataque
    fi = int(sr * 0.04)
    onda[:fi] *= np.linspace(0, 1, fi)
    return (np.clip(onda, -1.0, 1.0) * vol * 32767).astype(np.int16)


def reproducir(tipo: str = "campana") -> None:
    """Inicia la reproducción en un hilo daemon para no bloquear la UI."""
    if not DISPONIBLE:
        return
    threading.Thread(target=_sync, args=(tipo,), daemon=True).start()


def _sync(tipo: str) -> None:
    try:
        if tipo == "silencio":
            return
        sr = 44100
        mono = _generar_campana(sr)
        stereo = np.column_stack((mono, mono))
        snd = pygame.sndarray.make_sound(stereo)

        if tipo == "progresiva":
            # Tres toques con volumen creciente (0.25 → 0.65 → 1.0)
            for vol in (0.25, 0.65, 1.0):
                snd.set_volume(vol)
                snd.play()
                pygame.time.wait(3000)
        else:
            # Tres toques a volumen pleno con pausa respiratoria entre ellos
            for _ in range(3):
                snd.set_volume(1.0)
                snd.play()
                pygame.time.wait(3000)
    except Exception:
        pass
