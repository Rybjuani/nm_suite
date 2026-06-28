#!/usr/bin/env python3
"""VAS Introspect — renderer-independent design audit by live Qt widget introspection.

VAS's image checks (visual_auditor_spec.py) compare two *renders* (Chromium
mockup PNG vs Qt capture PNG), so their ceiling is coarse — every fine property
(shadow, radius, shape, padding) dissolves into "render noise". This module
sidesteps that entirely: instead of looking at pixels, it walks the live Qt
widget tree at capture time and reads the *actually applied* visual state
(graphics effects, stylesheet, geometry, font, instance attributes), then checks
it against design contracts derived from the component specs/mockup.

Because it reads ground truth (not a render), there is no cross-renderer noise:
a divergence is real application debt, e.g. a card that never received its
drop-shadow, or a play button that the docstring says must be elevated but is
flat.

Used two ways:
  - During capture: capture_v8._grab_save calls audit_tree(win, surface_key) and
    accumulates findings into a sidecar report.
  - Standalone: build a window (NM_VISUAL_QA + offscreen) and call audit_tree.

No image processing, no OCR. Only PyQt6 introspection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

try:  # PyQt6 is only importable inside the Qt process
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget
    from PyQt6.QtCore import QPoint
except Exception:  # pragma: no cover - import guard for tooling
    QWidget = object  # type: ignore
    QGraphicsDropShadowEffect = ()  # type: ignore


# Card-family components: per their specs these are elevated surfaces and must
# carry a drop-shadow. Subclasses of NMCard inherit the same contract. Cards are
# also identified by the shared convention objectName == "NMCard" (set by NMCard
# and by app-local QFrame cards), so _is_card() matches either signal.
CARD_CLASSES = {
    "NMCard",
    "NMSectionCard",
    "NMAvisoCard",
    "NMStatCard",
    "NMCardSecondary",
    "NMMetricCard",
    "NMFormPanel",
    "NMFeaturedCard",
    "NMChartPanel",
    "ModuleCard",  # app/home_qt.py dashboard tile
    # Verified debt: its own docstring calls it "(NMCard)" but it subclasses
    # QFrame, so it never inherits NMCard's drop-shadow. Audit confirmed 0/30
    # instances are elevated while all 10 sibling card classes are 100% — it
    # renders flat. Contracted so VAS flags it until it is reparented to NMCard.
    "_ReminderCardV3",  # app/modules/avisos_qt.py
}
CARD_OBJECT_NAME = "NMCard"


def _is_card(info: "WidgetInfo") -> bool:
    return info.cls in CARD_CLASSES or info.object_name == CARD_OBJECT_NAME

_RADIUS_RE = re.compile(r"border(?:-[a-z]+)?-radius\s*:\s*([0-9.]+)\s*px", re.IGNORECASE)
_BORDER_RE = re.compile(r"(?<![-a-z])border\s*:\s*([0-9.]+)\s*px", re.IGNORECASE)
_MIN_AUDIT_PX = 16  # ignore micro/zero-size widgets


@dataclass
class WidgetInfo:
    cls: str
    object_name: str
    x: int
    y: int
    w: int
    h: int
    visible: bool
    enabled: bool
    has_shadow: bool
    shadow_blur: float
    qss_radius: float | None
    has_gradient_bg: bool
    border_px: float | None
    shape_radius_attr: Any  # NMAvatar._radius / NMCard._radius_override (None or int)
    disabled_attr: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "cls": self.cls,
            "object_name": self.object_name,
            "rect": [self.x, self.y, self.w, self.h],
            "visible": self.visible,
            "enabled": self.enabled,
            "has_shadow": self.has_shadow,
            "shadow_blur": round(self.shadow_blur, 1),
            "qss_radius": self.qss_radius,
            "has_gradient_bg": self.has_gradient_bg,
            "border_px": self.border_px,
            "shape_radius_attr": self.shape_radius_attr,
        }


def _shadow_of(widget: QWidget) -> tuple[bool, float]:
    eff = widget.graphicsEffect()
    if isinstance(eff, QGraphicsDropShadowEffect) and eff.isEnabled() and eff.blurRadius() > 0:
        return True, float(eff.blurRadius())
    return False, 0.0


def _parse_qss(qss: str) -> tuple[float | None, bool, float | None]:
    radius = None
    matches = _RADIUS_RE.findall(qss or "")
    if matches:
        radius = max(float(m) for m in matches)
    gradient = "qlineargradient" in (qss or "").lower() or "qradialgradient" in (qss or "").lower()
    border = None
    bm = _BORDER_RE.findall(qss or "")
    if bm:
        border = max(float(m) for m in bm)
    return radius, gradient, border


def introspect_widget(widget: QWidget, root: QWidget) -> WidgetInfo:
    has_shadow, blur = _shadow_of(widget)
    radius, gradient, border = _parse_qss(widget.styleSheet())
    try:
        top_left = widget.mapTo(root, QPoint(0, 0))
        x, y = top_left.x(), top_left.y()
    except Exception:
        x = y = -1
    geo = widget.geometry()
    # shape attribute: NMAvatar uses _radius, NMCard uses _radius_override
    shape_attr = getattr(widget, "_radius", getattr(widget, "_radius_override", None))
    return WidgetInfo(
        cls=type(widget).__name__,
        object_name=widget.objectName() or "",
        x=x,
        y=y,
        w=geo.width(),
        h=geo.height(),
        visible=widget.isVisible(),
        enabled=widget.isEnabled(),
        has_shadow=has_shadow,
        shadow_blur=blur,
        qss_radius=radius,
        has_gradient_bg=gradient,
        border_px=border,
        shape_radius_attr=shape_attr,
        disabled_attr=bool(getattr(widget, "_disabled", False)),
    )


def introspect_tree(root: QWidget) -> list[tuple[WidgetInfo, QWidget]]:
    """Walk root + descendants, returning (info, widget) for each real widget."""
    out: list[tuple[WidgetInfo, QWidget]] = []
    widgets = [root, *root.findChildren(QWidget)]
    for w in widgets:
        try:
            if not w.isVisible():
                continue
            geo = w.geometry()
            if geo.width() < _MIN_AUDIT_PX or geo.height() < _MIN_AUDIT_PX:
                continue
            out.append((introspect_widget(w, root), w))
        except Exception:
            continue
    return out


# ── Contracts ─────────────────────────────────────────────────────────────────
# Each contract inspects one widget and returns a divergence dict or None. They
# encode design intent and are deliberately conservative (skip disabled/edge
# cases) so a fired contract is real debt, not noise.


def _contract_card_shadow(info: WidgetInfo) -> dict[str, Any] | None:
    if not _is_card(info):
        return None
    if not info.visible or not info.enabled or info.disabled_attr:
        return None
    if info.has_shadow:
        return None
    return {
        "kind": "SHADOW_MISSING",
        "component": info.cls,
        "object_name": info.object_name,
        "rect": [info.x, info.y, info.w, info.h],
        "severity": "high",
        "message": f"{info.cls} is an elevated surface but has no drop-shadow (renders flat)",
    }


def _contract_playbutton_shadow(info: WidgetInfo) -> dict[str, Any] | None:
    # NMPlayButton spec: "sombra suave v3_shadow('sm')". Flag if a visible,
    # enabled instance carries no drop-shadow effect.
    if info.cls != "NMPlayButton":
        return None
    if not info.visible or not info.enabled or info.disabled_attr:
        return None
    if info.has_shadow:
        return None
    return {
        "kind": "SHADOW_MISSING",
        "component": info.cls,
        "object_name": info.object_name,
        "rect": [info.x, info.y, info.w, info.h],
        "severity": "medium",
        "message": "NMPlayButton spec requires a soft shadow but has none (renders flat)",
    }


def _contract_radius_present(info: WidgetInfo) -> dict[str, Any] | None:
    """Cards and avatars must carry a border-radius (QSS or shape attr).

    A flat rectangle on an NMCard/NMAvatar is debt — the mockup always rounds
    these surfaces. We skip widgets where a radius is set via either QSS
    ``border-radius`` or the ``_radius``/``_radius_override`` shape attribute.
    """
    if not _is_card(info) and info.cls != "NMAvatar":
        return None
    if not info.visible or not info.enabled or info.disabled_attr:
        return None
    if info.qss_radius is not None and info.qss_radius > 0:
        return None
    if info.shape_radius_attr is not None and float(info.shape_radius_attr) > 0:
        return None
    return {
        "kind": "RADIUS_MISSING",
        "component": info.cls,
        "object_name": info.object_name,
        "rect": [info.x, info.y, info.w, info.h],
        "severity": "medium",
        "message": f"{info.cls} has no border-radius (renders as sharp rectangle)",
    }


def _contract_gradient_when_specified(info: WidgetInfo) -> dict[str, Any] | None:
    """Flag NMCard widgets that look like hero/score surfaces but lack a gradient.

    The mockup uses gradients on prominent cards (hero score, dbt cards). If an
    NMCard is large (>= 280px wide AND >= 80px tall) and has neither a gradient
    nor a drop-shadow, it is likely a flat rectangle where the mockup intended
    depth. Conservative: only fires on size-qualified NMCard instances.
    """
    if not _is_card(info):
        return None
    if not info.visible or not info.enabled or info.disabled_attr:
        return None
    if info.has_gradient_bg or info.has_shadow:
        return None
    if info.w < 280 or info.h < 80:
        return None
    return {
        "kind": "GRADIENT_LIKELY_MISSING",
        "component": info.cls,
        "object_name": info.object_name,
        "rect": [info.x, info.y, info.w, info.h],
        "severity": "low",
        "message": f"{info.cls} ({info.w}x{info.h}) is a large card with no gradient and no shadow — mockup likely intended depth here",
    }


CONTRACTS = (
    _contract_card_shadow,
    _contract_playbutton_shadow,
    _contract_radius_present,
    _contract_gradient_when_specified,
)


# ── Geometry contracts (parent/sibling-aware) ──────────────────────────────────
# The per-widget contracts above only see one widget at a time, so they catch
# elevation/shape debt but not layout debt (oversized controls, contention,
# overlaps). These geometry contracts read the *applied* Qt geometry of a widget
# relative to its parent and siblings — renderer-independent ground truth, so a
# fired contract is real layout debt (e.g. three footer buttons that don't fit
# their dialog because each carries a 180px min-width), never cross-render noise.
#
# They are deliberately conservative to keep zero false positives, matching the
# discipline of the shadow/radius contracts:
#   - only interactive CONTROL_CLASSES (buttons), which should never spill out of
#     their container nor render on top of a sibling;
#   - parents whose children legitimately exceed their bounds (scroll content)
#     or overlap by design (stacked pages, fade/overlay containers) are skipped;
#   - generous pixel tolerances so sub-pixel/rounding never fires.

CONTROL_CLASSES = {
    "NMButton",
    "NMButtonOutline",
    "NMButtonGhost",
    "NMButtonSoft",
    "NMIconButton",
}
# Containers where overflow/overlap of children is expected, not debt.
_GEOM_SKIP_PARENT = {
    "QScrollArea",
    "QStackedWidget",
    "NMFadeWidget",
    "NMToast",
}
_OVERFLOW_TOL = 3   # px a control may exceed its parent before it counts as spill
_OVERLAP_MIN = 3    # px of intersection (both axes) before two controls "overlap"


def _control_enabled(info: WidgetInfo) -> bool:
    return (
        info.cls in CONTROL_CLASSES
        and info.visible
        and info.enabled
        and not info.disabled_attr
    )


def _max_spill(child: WidgetInfo, parent: WidgetInfo) -> tuple[float, str]:
    """Largest amount (px) by which child exceeds parent on any edge, + which."""
    edges = {
        "left": parent.x - child.x,
        "right": (child.x + child.w) - (parent.x + parent.w),
        "top": parent.y - child.y,
        "bottom": (child.y + child.h) - (parent.y + parent.h),
    }
    edge = max(edges, key=edges.get)
    return edges[edge], edge


def geometry_divergences(
    pairs: list[tuple[WidgetInfo, QWidget]]
) -> list[dict[str, Any]]:
    """Run parent/sibling geometry contracts over the introspected tree."""
    out: list[dict[str, Any]] = []
    by_id: dict[int, WidgetInfo] = {id(w): info for info, w in pairs}
    children_by_parent: dict[int, list[WidgetInfo]] = {}
    for info, w in pairs:
        p = w.parentWidget()
        if p is not None:
            children_by_parent.setdefault(id(p), []).append(info)

    # OVERFLOW — a control spilling beyond its direct parent's bounds.
    for info, w in pairs:
        if not _control_enabled(info):
            continue
        p = w.parentWidget()
        if p is None:
            continue
        pinfo = by_id.get(id(p))
        if pinfo is None or pinfo.cls in _GEOM_SKIP_PARENT:
            continue
        spill, edge = _max_spill(info, pinfo)
        if spill > _OVERFLOW_TOL:
            out.append({
                "kind": "GEOMETRY_OVERFLOW",
                "component": info.cls,
                "object_name": info.object_name,
                "rect": [info.x, info.y, info.w, info.h],
                "severity": "high",
                "message": (
                    f"{info.cls} overflows its {pinfo.cls} parent by {int(spill)}px "
                    f"on the {edge} (control {info.w}x{info.h} vs parent "
                    f"{pinfo.w}x{pinfo.h}) — layout contention/oversize"
                ),
            })

    # OVERLAP — two sibling controls whose rects intersect (rendered on top of
    # each other). Adjacency (0px gap) does not fire; only real intersection.
    for kids in children_by_parent.values():
        ctrls = [i for i in kids if _control_enabled(i)]
        for a in range(len(ctrls)):
            for b in range(a + 1, len(ctrls)):
                ia, ib = ctrls[a], ctrls[b]
                ix = min(ia.x + ia.w, ib.x + ib.w) - max(ia.x, ib.x)
                iy = min(ia.y + ia.h, ib.y + ib.h) - max(ia.y, ib.y)
                if ix > _OVERLAP_MIN and iy > _OVERLAP_MIN:
                    out.append({
                        "kind": "GEOMETRY_OVERLAP",
                        "component": f"{ia.cls}+{ib.cls}",
                        "object_name": f"{ia.object_name}|{ib.object_name}",
                        "rect": [
                            max(ia.x, ib.x), max(ia.y, ib.y), int(ix), int(iy),
                        ],
                        "severity": "high",
                        "message": (
                            f"{ia.cls} and {ib.cls} overlap by {int(ix)}x{int(iy)}px "
                            "(controls rendered on top of each other)"
                        ),
                    })
    return out


_INVENTORY_TOKENS = ("Card", "Check", "Avatar", "Button", "Toggle", "Chip", "Tile", "Ring", "Panel")


def _is_semantic(cls: str) -> bool:
    """Components worth recording in the design inventory (cards, controls…)."""
    return cls.startswith("NM") or any(tok in cls for tok in _INVENTORY_TOKENS)


def audit_tree(root: QWidget, surface_key: str = "") -> dict[str, Any]:
    """Introspect the tree, run contracts, and build a design inventory.

    Returns both contract failures (high-confidence debt) and a renderer-
    independent inventory of every semantic component's actually-applied visual
    state. The inventory is the raw signal an agent can diff against the mockup
    to find debt in areas no contract covers yet — e.g. an app-local card class
    that carries no shadow (flag for review: elevated debt, or flat by design?).
    """
    infos = introspect_tree(root)
    divergences: list[dict[str, Any]] = []
    # Parent/sibling geometry contracts (overflow, overlap) need the full tree
    # with widget handles, so they run as a batch over `infos` rather than in the
    # per-widget loop below.
    divergences.extend(geometry_divergences(infos))
    counts: dict[str, int] = {}
    inventory: dict[str, dict[str, Any]] = {}
    for info, _w in infos:
        counts[info.cls] = counts.get(info.cls, 0) + 1
        for contract in CONTRACTS:
            d = contract(info)
            if d:
                divergences.append(d)
        if _is_semantic(info.cls):
            inv = inventory.setdefault(
                info.cls,
                {"count": 0, "with_shadow": 0, "qss_radii": set(), "shape_attrs": set()},
            )
            inv["count"] += 1
            if info.has_shadow:
                inv["with_shadow"] += 1
            if info.qss_radius is not None:
                inv["qss_radii"].add(info.qss_radius)
            inv["shape_attrs"].add(info.shape_radius_attr)
    # make inventory JSON-serializable
    inv_out = {
        cls: {
            "count": v["count"],
            "with_shadow": v["with_shadow"],
            "qss_radii": sorted(v["qss_radii"]),
            "shape_attrs": sorted(str(s) for s in v["shape_attrs"]),
        }
        for cls, v in sorted(inventory.items())
    }
    return {
        "surface_key": surface_key,
        "widgets_audited": len(infos),
        "component_counts": counts,
        "inventory": inv_out,
        "divergences": divergences,
        "fail_count": len(divergences),
    }
