"""
PoELens Visual Preview
======================
Launches the real overlay over a procedurally-generated PoE-style game scene
so you can visually test and iterate on the overlay appearance without having
the game running.

Usage:
    python preview.py                           # procedural PoE background
    python preview.py --screenshot path.png     # use a real screenshot as background

Controls:
    Escape / close background window — exit preview
"""

import sys
import math
import random
import argparse

from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QBrush, QPen, QFont, QPixmap, QPainterPath,
)

# ── Stub modules — implement the minimum interface the HUD panels need ────────

class _AppStateStub:
    def __init__(self):
        self._profile = {
            "completed_quests": [],
            "crafting_queue": [],
            "current_zone": "Lioneye's Watch",
            "currency_session_start": None,
        }
        self._callbacks = {}

    def get(self, key, default=None):
        return self._profile.get(key, default)

    def set_zone(self, zone):
        self._profile["current_zone"] = zone

    def uncomplete_quest(self, quest_id):
        pass

    def add_observer(self, key, cb):
        self._callbacks.setdefault(key, []).append(cb)

    @property
    def currency_session_start(self):
        return None


class _QuestTrackerStub:
    def on_update(self, cb): pass

    def get_status(self):
        return [
            {"id": "q1", "act": 1, "name": "Breaking Some Eggs",      "completed": True,  "passive_points": 1},
            {"id": "q2", "act": 1, "name": "The Caged Brute",          "completed": True,  "passive_points": 1},
            {"id": "q3", "act": 1, "name": "The Marooned Mariner",     "completed": True,  "passive_points": 1},
            {"id": "q4", "act": 2, "name": "Through Sacred Ground",    "completed": True,  "passive_points": 2},
            {"id": "q5", "act": 2, "name": "Deal with the Bandits",    "completed": True,  "passive_points": 2},
            {"id": "q6", "act": 3, "name": "Sever the Right Hand",     "completed": False, "passive_points": 1},
            {"id": "q7", "act": 3, "name": "Fiery Knives",             "completed": False, "passive_points": 1},
            {"id": "q8", "act": 4, "name": "An Indomitable Spirit",    "completed": False, "passive_points": 1},
            {"id": "q9", "act": 5, "name": "Death to Purity",          "completed": False, "passive_points": 1},
        ]

    def get_point_totals(self):
        completed = sum(1 for q in self.get_status() if q["completed"])
        total     = sum(q["passive_points"] for q in self.get_status())
        earned    = sum(q["passive_points"] for q in self.get_status() if q["completed"])
        return {"earned": earned, "deducted": 0, "net": earned,
                "remaining": total - earned, "total_available": total}

    def get_next_quest(self):
        for q in self.get_status():
            if not q["completed"]:
                return {
                    "act": q["act"],
                    "name": q["name"],
                    "passive_points": q["passive_points"],
                    "steps": ["Travel to Act " + str(q["act"]), "Complete the quest"],
                }
        return None

    def manually_complete(self, quest_id):   pass
    def manually_uncomplete(self, quest_id): pass


class _PriceCheckerStub:
    def on_result(self, cb):            pass
    def on_currency_detected(self, cb): pass
    def check(self):                    pass


class _CurrencyTrackerStub:
    def on_update(self, cb): pass

    def get_last_amounts(self):
        return {"Chaos Orb": 842, "Divine Orb": 12, "Exalted Orb": 3, "Orb of Alteration": 204}

    def get_display_data(self):
        return {
            "session_start": None,
            "rates": [
                {"name": "Chaos Orb",   "count": 842, "chaos_rate": 85.0, "chaos_value": 1.0},
                {"name": "Divine Orb",  "count": 12,  "chaos_rate": 45.2, "chaos_value": 220.0},
                {"name": "Exalted Orb", "count": 3,   "chaos_rate": 8.1,  "chaos_value": 95.0},
            ],
            "chaos_rates": {"Chaos Orb": 85.0, "Divine Orb": 45.2, "Exalted Orb": 8.1},
            "total_chaos_per_hr": 138.3,
            "elapsed_minutes": 67.0,
        }

    def get_historical_display_data(self, days=None):
        return {"average_chaos_per_hr": 312.5, "session_count": 14, "chaos_rates": {}}

    def get_session_stats(self, days=None):
        return {"snapshot_count": 4, "total_hours": 1.12, "average_chaos_per_hr": 312.5}

    def start_session(self, amounts):  pass
    def snapshot(self, amounts):       pass


class _CraftingModuleStub:
    def on_update(self, cb): pass

    def list_methods(self):
        return [
            {"id": "alteration", "name": "Alteration Spam",  "description": "Spam Alterations for a specific prefix/suffix.",
             "steps": ["Transmute the item", "Alt spam until you hit the mod", "Augment if needed"],
             "notes": "Cheap for common mods. Expensive for rare combos.", "fossil_guide": {}},
            {"id": "essence",    "name": "Essence Crafting", "description": "Guarantee one mod, then fill the rest.",
             "steps": ["Choose your Essence", "Apply to normal item", "Craft remaining mods"],
             "notes": "Best for guaranteed T1 mods you can build around.", "fossil_guide": {}},
            {"id": "fossil",     "name": "Fossil Crafting",  "description": "Shape the mod pool using fossils.",
             "steps": ["Choose fossils for your tag", "Socket in resonator", "Apply to item"],
             "notes": "Powerful for complex mod combinations.", "fossil_guide": {}},
        ]

    def get_method_cost(self, method_id):
        return {"total_chaos": 45.0, "line_items": [
            {"name": "Orb of Alteration", "qty": 50, "chaos_total": 25.0, "acquire_via": ["Trade", "Vendor"]},
            {"name": "Orb of Augmentation","qty": 10, "chaos_total": 5.0,  "acquire_via": ["Trade"]},
        ]}

    def add_task(self, item_name, method_id, qty): pass
    def complete_task(self, index):                pass
    def remove_task(self, index):                  pass

    def get_queue(self):
        return [
            {"item_name": "Hunter Hubris Circlet", "method_id": "fossil",  "quantity": 1, "completed": False,
             "cost": {"total_chaos": 120.0, "method_name": "Fossil Crafting"}},
            {"item_name": "Crusader Chest",         "method_id": "essence", "quantity": 1, "completed": False,
             "cost": {"total_chaos": 85.0,  "method_name": "Essence Crafting"}},
        ]

    def get_total_queue_cost(self):
        return {"total_chaos": 205.0, "pending_tasks": 2}


class _MapOverlayStub:
    def on_update(self, cb): pass

    def get_current_zone(self):
        return {
            "name": "The Burial Chambers",
            "info": {
                "type":        "map",
                "area_level":  74,
                "waypoint":    True,
                "act":         None,
                "tier":        9,
                "boss":        "The Plagued",
                "notes":       "High density. Boss has strong Bleed and Poison.",
            },
        }

    def get_history(self):
        zones = [
            ("Lioneye's Watch",      "town",    1,   None, None),
            ("The Ledge",            "map",     73,  8,    "Ironpoint the Forsaken"),
            ("The Vault",            "map",     76,  11,   "Ephij"),
            ("The Haunted Mansion",  "map",     77,  12,   "The Bone Sculptor"),
            ("The Burial Chambers",  "map",     74,  9,    "The Plagued"),
        ]
        import time
        now = time.time()
        result = []
        for i, (name, ztype, lvl, tier, boss) in enumerate(zones):
            result.append({
                "name":      name,
                "info":      {"type": ztype, "area_level": lvl, "tier": tier, "boss": boss,
                              "waypoint": True, "act": None, "notes": ""},
                "timestamp": now - (len(zones) - i) * 420,
            })
        return result

    def handle_zone_change(self, data): pass


class _XPTrackerStub:
    def on_update(self, cb): pass

    def get_display_data(self):
        return {
            "started":         True,
            "char_name":       "GlacialCascadeHC",
            "level":           91,
            "baseline_level":  90,
            "xp_this_session": 18_432_100,
            "xp_per_hr":       55_000_000,
            "elapsed_minutes": 67.0,
            "time_to_level":   2.8,
        }

    def start_session(self, league, on_started): on_started(True, "Preview mode")
    def poll(self):                              pass
    def handle_zone_change(self, data):          pass


class _ChaosRecipeStub:
    def on_update(self, cb): pass

    def get_sets(self):
        return {"chaos": 3, "regal": 1, "any": 5}

    def get_slot_status(self):
        return {
            "Helmet": {"chaos": 2, "regal": 1}, "Body Armour": {"chaos": 1, "regal": 1},
            "Gloves":  {"chaos": 3, "regal": 0}, "Boots": {"chaos": 2, "regal": 1},
            "Belt":    {"chaos": 1, "regal": 0}, "Ring":  {"chaos": 4, "regal": 2},
            "Amulet":  {"chaos": 1, "regal": 0}, "Weapon": {"chaos": 2, "regal": 1},
        }

    def scan(self, league, on_done): on_done([], None)


# ── Procedural PoE-style background ──────────────────────────────────────────

_STONE_SEED = 42  # fixed seed for reproducible tile variance


class PoEBackground(QWidget):
    """
    Full-screen procedural PoE-like game background.
    Draws: game world (stone floor, atmospheric lighting, vignette) +
           bottom UI bar (health/mana orbs, flasks, skill bar, exp bar).
    """

    GOLD      = QColor(0xb8, 0x87, 0x30)
    GOLD_LITE = QColor(0xe2, 0xb9, 0x6f)
    DARK_UI   = QColor(0x08, 0x08, 0x0c)
    ORB_BORDER= QColor(0x8a, 0x64, 0x28)

    def __init__(self, screenshot_path: str | None = None, cmd_palette=None):
        super().__init__()
        self._cmd_palette = cmd_palette
        self._screenshot: QPixmap | None = None
        if screenshot_path:
            px = QPixmap(screenshot_path)
            if not px.isNull():
                self._screenshot = px
            else:
                print(f"[preview] Could not load screenshot: {screenshot_path!r} — using procedural background")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        # Pre-compute tile variance once (fixed seed for consistency)
        rng = random.Random(_STONE_SEED)
        self._tile_var = [rng.uniform(-0.04, 0.04) for _ in range(64 * 36)]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()
        elif event.key() == Qt.Key.Key_QuoteLeft:   # backtick
            if self._cmd_palette is not None:
                self._cmd_palette.toggle()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self._screenshot:
            self._paint_screenshot(p, w, h)
        else:
            self._paint_world(p, w, h)

        self._paint_bottom_ui(p, w, h)
        p.end()

    # ------------------------------------------------------------------
    # Screenshot mode

    def _paint_screenshot(self, p: QPainter, w: int, h: int):
        scaled = self._screenshot.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Centre-crop
        ox = (scaled.width()  - w) // 2
        oy = (scaled.height() - h) // 2
        p.drawPixmap(0, 0, scaled, ox, oy, w, h)

    # ------------------------------------------------------------------
    # Procedural world

    def _paint_world(self, p: QPainter, w: int, h: int):
        ui_h     = int(h * 0.195)   # bottom UI panel height
        world_h  = h - ui_h

        # 1. Stone floor base gradient
        bg = QLinearGradient(0, 0, 0, world_h)
        bg.setColorAt(0.0, QColor(0x12, 0x0e, 0x09))
        bg.setColorAt(0.4, QColor(0x18, 0x14, 0x0e))
        bg.setColorAt(1.0, QColor(0x0e, 0x0b, 0x07))
        p.fillRect(0, 0, w, world_h, bg)

        # 2. Stone tile grid
        tile = max(int(w / 26), 40)
        pen  = QPen(QColor(0x22, 0x1c, 0x14, 80))
        pen.setWidth(1)
        p.setPen(pen)
        rng  = self._tile_var
        idx  = 0
        for ty in range(0, world_h + tile, tile):
            for tx in range(0, w + tile, tile):
                var   = rng[idx % len(rng)]
                shade = int(min(255, max(0, (0x1a + var * 255))))
                col   = QColor(shade, int(shade * 0.88), int(shade * 0.72), 255)
                p.fillRect(tx, ty, tile - 1, tile - 1, col)
                idx += 1
        # Tile border lines
        for tx in range(0, w + tile, tile):
            p.drawLine(tx, 0, tx, world_h)
        for ty in range(0, world_h + tile, tile):
            p.drawLine(0, ty, w, ty)

        # 3. Warm torchlight (two point sources)
        for lx, ly, r, a in [
            (w * 0.35, world_h * 0.45, w * 0.40, 55),
            (w * 0.70, world_h * 0.30, w * 0.28, 35),
        ]:
            torch = QRadialGradient(lx, ly, r)
            torch.setColorAt(0.0, QColor(0xd4, 0x8a, 0x10, a))
            torch.setColorAt(0.5, QColor(0x80, 0x50, 0x08, a // 2))
            torch.setColorAt(1.0, QColor(0x00, 0x00, 0x00, 0))
            p.fillRect(0, 0, w, world_h, torch)

        # 4. Some scattered "debris" dots on the floor
        rng2 = random.Random(77)
        for _ in range(180):
            dx = rng2.randint(0, w)
            dy = rng2.randint(int(world_h * 0.25), world_h - 4)
            ds = rng2.randint(1, 3)
            da = rng2.randint(30, 90)
            p.fillRect(dx, dy, ds, ds, QColor(0x40, 0x30, 0x18, da))

        # 5. A few dark "monster" silhouettes in the mid-ground
        self._draw_monsters(p, w, world_h)

        # 6. Vignette — dark radial gradient from screen edges
        vig = QRadialGradient(w / 2, world_h / 2, max(w, world_h) * 0.65)
        vig.setColorAt(0.0, QColor(0, 0, 0, 0))
        vig.setColorAt(0.6, QColor(0, 0, 0, 40))
        vig.setColorAt(1.0, QColor(0, 0, 0, 180))
        p.fillRect(0, 0, w, world_h, vig)

        # 7. Thin atmospheric mist layer at the bottom of the world
        mist = QLinearGradient(0, world_h - int(h * 0.06), 0, world_h)
        mist.setColorAt(0.0, QColor(0x08, 0x0c, 0x14, 0))
        mist.setColorAt(1.0, QColor(0x04, 0x06, 0x10, 120))
        p.fillRect(0, world_h - int(h * 0.06), w, int(h * 0.06), mist)

    def _draw_monsters(self, p: QPainter, w: int, world_h: int):
        """Draw 2-3 vague humanoid silhouettes in the game world."""
        rng = random.Random(13)
        for _ in range(3):
            mx = rng.randint(int(w * 0.15), int(w * 0.72))
            my = rng.randint(int(world_h * 0.38), int(world_h * 0.65))
            scale = rng.uniform(0.7, 1.1)
            alpha = rng.randint(55, 100)
            self._draw_silhouette(p, mx, my, scale, alpha)

    def _draw_silhouette(self, p: QPainter, cx: int, cy: int, scale: float, alpha: int):
        path = QPainterPath()
        s = scale
        # Head
        path.addEllipse(QRectF(cx - 7*s, cy - 40*s, 14*s, 14*s))
        # Body
        path.addRect(QRectF(cx - 10*s, cy - 26*s, 20*s, 26*s))
        # Left leg
        path.addRect(QRectF(cx - 10*s, cy,       9*s, 22*s))
        # Right leg
        path.addRect(QRectF(cx + 1*s,  cy,       9*s, 22*s))
        # Left arm
        path.addRect(QRectF(cx - 18*s, cy - 26*s, 8*s, 18*s))
        # Right arm
        path.addRect(QRectF(cx + 10*s, cy - 26*s, 8*s, 18*s))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0x06, 0x03, 0x08, alpha)))
        p.drawPath(path)

        # Add subtle red eyes
        p.setBrush(QBrush(QColor(0xcc, 0x10, 0x10, alpha + 40)))
        eye_y = cy - 33 * scale
        eye_r = max(2, int(2 * scale))
        p.drawEllipse(QRectF(cx - 4*scale, eye_y, eye_r, eye_r))
        p.drawEllipse(QRectF(cx + 2*scale, eye_y, eye_r, eye_r))

    # ------------------------------------------------------------------
    # Bottom UI bar

    def _paint_bottom_ui(self, p: QPainter, w: int, h: int):
        ui_h     = int(h * 0.195)
        ui_y     = h - ui_h
        orb_r    = int(ui_h * 0.42)
        orb_cy   = ui_y + int(ui_h * 0.44)

        # ── Dark background panel ─────────────────────────────────────
        panel_grad = QLinearGradient(0, ui_y, 0, h)
        panel_grad.setColorAt(0.0, QColor(0x04, 0x04, 0x08, 240))
        panel_grad.setColorAt(1.0, QColor(0x00, 0x00, 0x00, 255))
        p.fillRect(0, ui_y, w, ui_h, panel_grad)

        # Top divider line (gold)
        p.setPen(QPen(QColor(0x6a, 0x4c, 0x18, 180), 1))
        p.drawLine(0, ui_y, w, ui_y)

        # ── Health orb (left) ─────────────────────────────────────────
        hx = int(w * 0.077)
        self._draw_orb(p, hx, orb_cy, orb_r,
                       QColor(0x8b, 0x00, 0x00), QColor(0xd0, 0x20, 0x20),
                       "4,827", "/ 4,827", "Life")

        # ── Mana orb (right) ─────────────────────────────────────────
        mx = w - int(w * 0.077)
        self._draw_orb(p, mx, orb_cy, orb_r,
                       QColor(0x00, 0x00, 0x80), QColor(0x20, 0x60, 0xd0),
                       "1,840", "/ 1,840", "Mana")

        # ── 5 Flask slots (between orbs, left of centre) ──────────────
        self._draw_flasks(p, w, h, ui_y, ui_h, hx, orb_r)

        # ── 8 Skill slots (centred) ───────────────────────────────────
        self._draw_skill_bar(p, w, h, ui_y, ui_h)

        # ── Experience bar (very bottom) ──────────────────────────────
        bar_h   = max(4, int(h * 0.004))
        bar_y   = h - bar_h - 1
        p.fillRect(0, bar_y, w, bar_h, QColor(0x10, 0x08, 0x18))

        xp_fill = int(w * 0.61)   # 61% progress
        xp_grad = QLinearGradient(0, 0, xp_fill, 0)
        xp_grad.setColorAt(0.0, QColor(0x4a, 0x1a, 0x6a))
        xp_grad.setColorAt(0.6, QColor(0x7a, 0x30, 0xaa))
        xp_grad.setColorAt(1.0, QColor(0x9a, 0x50, 0xca))
        p.fillRect(0, bar_y, xp_fill, bar_h, xp_grad)

        # Exp bar border
        p.setPen(QPen(QColor(0x3a, 0x18, 0x50, 160), 1))
        p.drawRect(0, bar_y, w - 1, bar_h - 1)

        # Level label (bottom-left near exp bar)
        p.setFont(QFont("Segoe UI", max(7, int(h * 0.013)), QFont.Weight.Bold))
        p.setPen(QPen(QColor(0xb8, 0x87, 0x30, 200)))
        p.drawText(6, bar_y - 2, "Lv 91 — GlacialCascadeHC")

    def _draw_orb(self, p: QPainter, cx: int, cy: int, r: int,
                  col_dark: QColor, col_light: QColor,
                  val_top: str, val_bot: str, label: str):
        # Outer dark ring
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0x06, 0x04, 0x02)))
        p.drawEllipse(QRectF(cx - r - 4, cy - r - 4, (r + 4) * 2, (r + 4) * 2))

        # Gold border ring
        border_pen = QPen(self.ORB_BORDER, 3)
        p.setPen(border_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx - r - 2, cy - r - 2, (r + 2) * 2, (r + 2) * 2))

        # Orb fill (radial gradient)
        orb_grad = QRadialGradient(cx - r * 0.2, cy - r * 0.2, r * 1.1)
        orb_grad.setColorAt(0.0, col_light)
        orb_grad.setColorAt(0.5, col_dark)
        orb_grad.setColorAt(1.0, QColor(0x04, 0x02, 0x06))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(orb_grad)
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Highlight gleam (top-left arc)
        gleam = QRadialGradient(cx - r * 0.35, cy - r * 0.35, r * 0.55)
        gleam.setColorAt(0.0, QColor(255, 255, 255, 55))
        gleam.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(gleam)
        p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Text
        font_size = max(7, r // 5)
        p.setPen(QPen(QColor(0xe8, 0xd8, 0xb8, 220)))
        p.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))

        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(val_top)
        p.drawText(cx - tw // 2, cy - 2, val_top)

        p.setFont(QFont("Segoe UI", max(6, font_size - 1)))
        p.setPen(QPen(QColor(0xa8, 0x98, 0x80, 180)))
        tw2 = fm.horizontalAdvance(val_bot)
        p.drawText(cx - tw2 // 2, cy + fm.height(), val_bot)

        # Label below orb
        p.setFont(QFont("Segoe UI", max(6, font_size - 1)))
        p.setPen(QPen(self.GOLD, 200))
        lw = p.fontMetrics().horizontalAdvance(label)
        p.drawText(cx - lw // 2, cy + r + p.fontMetrics().height() + 4, label)

    def _draw_flasks(self, p: QPainter, w: int, h: int,
                     ui_y: int, ui_h: int, hx: int, orb_r: int):
        flask_colors = [
            (QColor(0xb0, 0x18, 0x18), QColor(0xf0, 0x40, 0x40)),  # Life
            (QColor(0xb0, 0x18, 0x18), QColor(0xf0, 0x40, 0x40)),  # Life
            (QColor(0x18, 0x18, 0xb0), QColor(0x40, 0x40, 0xf0)),  # Mana
            (QColor(0x20, 0x50, 0x10), QColor(0x40, 0xa8, 0x20)),  # Jade
            (QColor(0x50, 0x40, 0x08), QColor(0xc8, 0xa0, 0x18)),  # Quicksilver
        ]
        keys = ["1", "2", "3", "4", "5"]

        flask_x0 = hx + orb_r + int(w * 0.012)
        flask_w  = int(w * 0.028)
        flask_h  = int(ui_h * 0.62)
        flask_y  = ui_y + int(ui_h * 0.12)
        gap      = int(w * 0.008)

        for i, ((dark, light), key) in enumerate(zip(flask_colors, keys)):
            fx = flask_x0 + i * (flask_w + gap)

            # Outer border
            p.setPen(QPen(self.ORB_BORDER, 1))
            p.setBrush(QBrush(QColor(0x06, 0x04, 0x02)))
            p.drawRoundedRect(fx - 1, flask_y - 1, flask_w + 2, flask_h + 2, 3, 3)

            # Flask body (fill gradient)
            fg = QLinearGradient(fx, flask_y, fx, flask_y + flask_h)
            fg.setColorAt(0.0, dark)
            fg.setColorAt(1.0, light)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(fg)
            p.drawRoundedRect(fx, flask_y, flask_w, flask_h, 2, 2)

            # Gleam
            gleam = QLinearGradient(fx, flask_y, fx + flask_w * 0.4, flask_y)
            gleam.setColorAt(0.0, QColor(255, 255, 255, 40))
            gleam.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(gleam)
            p.drawRoundedRect(fx, flask_y, flask_w, flask_h, 2, 2)

            # Key number
            p.setFont(QFont("Segoe UI", max(7, flask_w // 3)))
            p.setPen(QPen(QColor(0xd8, 0xc8, 0xa0, 200)))
            p.drawText(fx, flask_y + flask_h + p.fontMetrics().height() + 1, key)

    def _draw_skill_bar(self, p: QPainter, w: int, h: int, ui_y: int, ui_h: int):
        slot_count = 8
        slot_size  = int(ui_h * 0.38)
        gap        = int(slot_size * 0.12)
        total_w    = slot_count * slot_size + (slot_count - 1) * gap
        sx0        = (w - total_w) // 2
        sy         = ui_y + int(ui_h * 0.45)

        skill_cols = [
            QColor(0x28, 0x18, 0x50),   # Cold — blue-purple
            QColor(0x28, 0x18, 0x50),
            QColor(0x18, 0x38, 0x18),   # Green
            QColor(0x40, 0x28, 0x08),   # Orange
            QColor(0x28, 0x18, 0x50),
            QColor(0x18, 0x18, 0x38),   # Blue
            QColor(0x38, 0x20, 0x08),   # Brown
            QColor(0x30, 0x10, 0x10),   # Red
        ]
        hotkeys = ["Q", "W", "E", "R", "T", "A", "S", "D"]

        for i in range(slot_count):
            sx = sx0 + i * (slot_size + gap)

            # Slot border
            p.setPen(QPen(self.ORB_BORDER, 1))
            p.setBrush(QBrush(QColor(0x06, 0x04, 0x02)))
            p.drawRect(sx - 1, sy - 1, slot_size + 2, slot_size + 2)

            # Slot fill
            sg = QLinearGradient(sx, sy, sx + slot_size, sy + slot_size)
            sg.setColorAt(0.0, skill_cols[i].lighter(130))
            sg.setColorAt(1.0, skill_cols[i])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(sg)
            p.drawRect(sx, sy, slot_size, slot_size)

            # Hotkey label bottom-right
            p.setFont(QFont("Segoe UI", max(6, slot_size // 4)))
            p.setPen(QPen(QColor(0xb8, 0xa8, 0x80, 200)))
            p.drawText(sx + slot_size - p.fontMetrics().horizontalAdvance(hotkeys[i]) - 2,
                       sy + slot_size - 2, hotkeys[i])


# ── Preview entry point ───────────────────────────────────────────────────────

def _make_stubs():
    """Return the stub instances the HUD needs."""
    import config as cfg
    conf = cfg.load()

    state            = _AppStateStub()
    quest_tracker    = _QuestTrackerStub()
    price_checker    = _PriceCheckerStub()
    currency_tracker = _CurrencyTrackerStub()
    crafting         = _CraftingModuleStub()
    map_overlay      = _MapOverlayStub()
    xp_tracker       = _XPTrackerStub()
    chaos_recipe     = _ChaosRecipeStub()

    return state, quest_tracker, price_checker, currency_tracker, crafting, \
           map_overlay, xp_tracker, chaos_recipe, conf


def main():
    parser = argparse.ArgumentParser(description="PoELens visual preview")
    parser.add_argument(
        "--screenshot", metavar="PATH",
        help="Path to a PoE screenshot to use as background (PNG, JPG)",
    )
    parser.add_argument(
        "--opacity", type=float, default=0.92, metavar="0.0-1.0",
        help="Overlay opacity (default 0.92)",
    )
    args = parser.parse_args()

    # Suppress hotkey / Client.txt errors in preview mode
    import os
    os.environ.setdefault("POELENS_PREVIEW", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("PoELens Preview")

    # ── Stubs ─────────────────────────────────────────────────────────
    (state, quest_tracker, price_checker, currency_tracker,
     crafting, map_overlay, xp_tracker, chaos_recipe, conf) = _make_stubs()

    conf["overlay_opacity"] = args.opacity

    # ── Command palette (created before bg so it can be passed in) ────
    from ui.widgets.command_palette import CommandPalette
    cmd_palette = CommandPalette()

    # ── Background window ─────────────────────────────────────────────
    bg = PoEBackground(args.screenshot, cmd_palette=cmd_palette)
    screen = app.primaryScreen().geometry()
    bg.setGeometry(screen)
    bg.show()

    # ── Real HUD over the background ──────────────────────────────────
    import ui.hud as hud_module
    hud = hud_module.HUD(
        state=state,
        quest_tracker=quest_tracker,
        price_checker=price_checker,
        currency_tracker=currency_tracker,
        crafting=crafting,
        map_overlay=map_overlay,
        xp_tracker=xp_tracker,
        chaos_recipe=chaos_recipe,
        config=conf,
        # OAuth-dependent panels show their "connect" placeholder — that is correct
        div_tracker=None,
        atlas_tracker=None,
        heist_planner=None,
        gem_planner=None,
        map_scanner=None,
        lab_tracker=None,
        currency_flip=None,
        oauth_manager=None,
        stash_api=None,
        character_api=None,
    )
    hud.show()

    # ── Zone popup demo — shows for 15s then fades ────────────────────
    from ui.widgets.zone_popup import ZonePopup
    zone_popup = ZonePopup(timeout_ms=15000)
    zone_popup.show_zone({
        "name": "The Burial Chambers",
        "tier": 9,
        "type": "map",
        "area_level": 74,
        "boss": "The Plagued",
        "notes": "High density · Boss has Bleed/Poison · Good for div card farming",
    })

    # ── Wire command palette actions ──────────────────────────────────
    def handle_command(cmd, args):
        if cmd == "zone":
            zone_popup.show_zone({
                "name": "The Burial Chambers", "tier": 9, "type": "map",
                "area_level": 74, "boss": "The Plagued",
                "notes": "High density · Boss has Bleed/Poison",
            })
        elif cmd == "help":
            cmd_palette.show()  # stay open after help
    cmd_palette.command_selected.connect(handle_command)

    # Keep background behind the overlay
    bg.lower()
    hud.raise_()

    # Pressing Escape on the background closes everything
    app.exec()


if __name__ == "__main__":
    main()
