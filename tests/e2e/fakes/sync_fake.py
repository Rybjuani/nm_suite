from __future__ import annotations


def patch_sync_noop(monkeypatch):
    import shared.sync as sync_module

    monkeypatch.setattr(sync_module, "sync_al_abrir", lambda *args, **kwargs: True)
    monkeypatch.setattr(sync_module, "sync_completo", lambda *args, **kwargs: True)
    monkeypatch.setattr(sync_module, "sync_inmediato", lambda *args, **kwargs: True)
    monkeypatch.setattr(sync_module, "sync_inmediato_background", lambda *args, **kwargs: None)
    monkeypatch.setattr(sync_module, "sync_en_background", lambda callback=None: callback(True) if callback else None)
    return sync_module


def patch_sync_returns(sb, monkeypatch):
    sync_module = patch_sync_noop(monkeypatch)
    if hasattr(sync_module, "_get_client"):
        monkeypatch.setattr(sync_module, "_get_client", lambda *args, **kwargs: sb)
    return sync_module
