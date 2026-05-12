"""base_module.py — Clase base para módulos de la plataforma paciente."""
import customtkinter as ctk
from shared.components import HeaderFrame, ThemeManager, aplicar_captionbar


class NMModule(ctk.CTkFrame):
    MODULE_TITLE: str = ""
    MODULE_ICON: str = ""

    def __init__(self, master, modo: str, theme_manager: ThemeManager, on_back):
        super().__init__(master, fg_color="transparent")
        self.modo = modo
        self.tm = theme_manager
        self._on_back = on_back
        self._build_header()
        self.build_ui()

    def _build_header(self):
        from shared.theme import COLORS, TYPOGRAPHY
        c = COLORS.get(self.modo, COLORS["dark_hybrid"])
        header = ctk.CTkFrame(self, fg_color=c["bg_secondary"], height=52, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        btn_back = ctk.CTkButton(
            header, text="←", width=40, height=36,
            fg_color="transparent", hover_color=c["bg_surface"],
            text_color=c["text_primary"],
            font=(TYPOGRAPHY["font_family"], 18),
            command=self._on_back,
        )
        btn_back.pack(side="left", padx=(12, 0), pady=8)
        ctk.CTkLabel(
            header, text=f"{self.MODULE_ICON}  {self.MODULE_TITLE}",
            font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_h3"], "bold"),
            text_color=c["text_primary"],
        ).pack(side="left", padx=12, pady=8)

    def build_ui(self):
        raise NotImplementedError

    def get_card_status(self) -> str:
        return ""

    def on_enter(self):
        pass

    def on_leave(self):
        pass
