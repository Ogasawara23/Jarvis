"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         J.A.R.V.I.S  —  INTEGRATED v8.1  (PySide6 + ElevenLabs)           ║
║  Assistente de voz • Rede de partículas • Motor de gestos híbrido           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  pip install mediapipe opencv-python numpy pyautogui                         ║
║  pip install SpeechRecognition psutil pycaw comtypes                         ║
║  pip install elevenlabs pygame PySide6                                       ║
║  pip install uiautomation pywin32                                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  MUDANÇAS v8.1 — ElevenLabs integrado                                       ║
║  • edge_tts substituído pela API oficial do ElevenLabs                      ║
║  • Modelo eleven_multilingual_v2 com voz configurável                       ║
║  • Cache em disco (mesmo hash → zero chamadas extras à API)                 ║
║  • Fallback automático para pyttsx3 se a API falhar                         ║
║  • Toda a lógica de voz encapsulada em ElevenLabsVoiceEngine                ║
║  • Resto do código 100% preservado (gestos, UI, overlay, etc.)              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ── Configuração ElevenLabs ───────────────────────────────────────────────────
ELEVENLABS_API_KEY  = "sk_84233d7a9ad0297a214f7a202f5f8b35a27d8c53a6caf760"
ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"   # Daniel — voz masculina compatível com plano gratuito
ELEVENLABS_MODEL    = "eleven_multilingual_v2"
ELEVENLABS_SETTINGS = {
    "stability":        0.55,
    "similarity_boost": 0.80,
    "style":            0.20,
    "use_speaker_boost": True,
}

# ── Parâmetros ajustáveis ─────────────────────────────────────────────────────
PARTICLE_COUNT      = 65
PARTICLE_SPEED      = 1.0
CONNECTION_DIST     = 140
PULSE_SPEED         = 0.045

# Gesture Engine v8 params
GESTURE_HOLD_FRAMES  = 8
GESTURE_COOLDOWN_SEC = 1.0
PINCH_THRESHOLD      = 0.048
# ─────────────────────────────────────────────────────────────────────────────

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QLineEdit, QTextEdit, QProgressBar,
    QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject, QPointF, QRect, QUrl
from PySide6.QtGui import (
    QFont, QColor, QPalette, QTextCursor, QPixmap, QImage,
    QPainter, QRadialGradient, QLinearGradient, QBrush, QPen,
)

import sys, threading, datetime, os, random, time, subprocess
import platform, socket, ctypes, queue, math
import tempfile, hashlib
from pathlib import Path

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import cv2
    import mediapipe as mp
    import numpy as np
    CV2_OK = True
except Exception:
    CV2_OK = True

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0
    AG_OK = True
except Exception:
    AG_OK = False

try:
    import psutil; PS_OK = True
except Exception:
    PS_OK = False

try:
    import speech_recognition as sr; SR_OK = True
except Exception:
    SR_OK = False

try:
    import pygame
    # Garante que o mixer está inicializado (evita conflito com o launcher)
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    PG_OK = True
except Exception:
    PG_OK = False

try:
    import webbrowser as wb; WB_OK = True
except Exception:
    WB_OK = False

try:
    import uiautomation as auto; AUTO_OK = True
except Exception:
    AUTO_OK = False

try:
    import win32gui, win32con; WIN32_OK = True
except Exception:
    WIN32_OK = False

# ── Módulo de Clima ───────────────────────────────────────────────────────────
try:
    from Jarvis_Clima import cmd_clima, PALAVRAS_CLIMA
    CLIMA_OK = True
except Exception:
    CLIMA_OK = False
    PALAVRAS_CLIMA = []

# ── ElevenLabs ────────────────────────────────────────────────────────────────
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    _eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    ELEVEN_OK = True
except Exception:
    ELEVEN_OK = False
    _eleven_client = None


# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
class DS:
    BG0 = "#030810"
    BG1 = "#060D1A"
    BG2 = "#0A1424"

    BLUE        = "#1A8FFF"
    BLUE_BRIGHT = "#4DB8FF"
    BLUE_DIM    = "#0A2040"
    BLUE_MID    = "#0D5099"
    BLUE_GLOW   = "#00AAFF"

    CYAN        = "#00D4FF"
    CYAN_DIM    = "#002A38"

    GREEN  = "#00E5A0"
    RED    = "#FF3358"
    YELLOW = "#FFD166"
    AMBER  = "#FF8C00"

    T1 = "#D0E8FF"
    T2 = "#5A7A99"
    T3 = "#1A3050"

    BORDER      = "#0D1E30"
    BORDER_BLUE = "#0D3060"

    FONT_DISPLAY = "Orbitron, Rajdhani, Consolas, monospace"
    FONT_MONO    = "JetBrains Mono, Consolas, monospace"
    FONT_UI      = "Segoe UI, SF Pro Display, system-ui, sans-serif"


GLOBAL_QSS = f"""
QMainWindow, QWidget {{
    background: {DS.BG0};
    color: {DS.T1};
    font-family: {DS.FONT_UI};
    font-size: 13px;
}}
QScrollBar:vertical {{
    background: {DS.BG1}; width: 4px; margin: 0; border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {DS.BLUE_DIM}; border-radius: 2px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {DS.BLUE_MID}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
QTextEdit {{
    background: transparent; border: none;
    color: {DS.T1}; font-family: {DS.FONT_MONO}; font-size: 10px;
    selection-background-color: {DS.BLUE_DIM};
}}
QLineEdit {{
    background: {DS.BG2}; border: 1px solid {DS.BORDER_BLUE};
    border-radius: 6px; color: {DS.T1};
    font-family: {DS.FONT_MONO}; font-size: 12px; padding: 0 10px;
}}
QLineEdit:focus {{ border-color: {DS.BLUE}; }}
QToolTip {{
    background: {DS.BG2}; border: 1px solid {DS.BORDER_BLUE};
    color: {DS.T1}; padding: 4px 8px; border-radius: 4px;
}}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# PARTICLE
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    def __init__(self, cx: float, cy: float, radius: float):
        self.reset(cx, cy, radius)

    def reset(self, cx: float, cy: float, radius: float):
        theta = random.uniform(0, 2 * math.pi)
        phi   = random.uniform(0, math.pi)
        r     = random.uniform(0.25, 1.0) * radius

        self.x3 = r * math.sin(phi) * math.cos(theta)
        self.y3 = r * math.sin(phi) * math.sin(theta)
        self.z3 = r * math.cos(phi)

        self.vt = random.uniform(-0.012, 0.012) * PARTICLE_SPEED
        self.vp = random.uniform(-0.010, 0.010) * PARTICLE_SPEED

        self._osc_freq  = random.uniform(0.8, 2.5)
        self._osc_phase = random.uniform(0, 2 * math.pi)
        self._osc_amp   = random.uniform(0.05, 0.18)

        self._r0    = r
        self._theta = theta
        self._phi   = phi
        self.alpha  = random.uniform(0.5, 1.0)
        self.size   = random.uniform(1.8, 4.0)

    def update(self, state: str, t: float):
        speed_mult = {
            "idle":       1.0,
            "listening":  1.8,
            "processing": 2.8,
            "speaking":   1.4,
        }.get(state, 1.0)

        self._theta += self.vt * speed_mult
        self._phi   += self.vp * speed_mult

        osc_r = self._r0 * (1.0 + self._osc_amp * math.sin(
            t * self._osc_freq + self._osc_phase
        ))

        self.x3 = osc_r * math.sin(self._phi) * math.cos(self._theta)
        self.y3 = osc_r * math.sin(self._phi) * math.sin(self._theta)
        self.z3 = osc_r * math.cos(self._phi)

    def project(self, cx: float, cy: float, fov: float = 400):
        z = self.z3 + fov
        if z < 1: z = 1
        scale = fov / z
        px = cx + self.x3 * scale
        py = cy + self.y3 * scale
        depth = (self.z3 + self._r0) / (2 * self._r0)
        return px, py, scale, depth


# ═══════════════════════════════════════════════════════════════════════════════
# NETWORK WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
class NetworkWidget(QWidget):
    IDLE       = "idle"
    LISTENING  = "listening"
    PROCESSING = "processing"
    SPEAKING   = "speaking"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(460, 460)

        self._state  = self.IDLE
        self._pulse  = 0.0
        self._wave   = 0.0
        self._wave2  = 0.0
        self._angle  = 0.0
        self._t      = 0.0

        self._particles: list[Particle] = []
        self._init_particles()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _init_particles(self):
        cx = self.width()  / 2
        cy = self.height() / 2
        R  = min(cx, cy) * 0.82
        self._particles = [Particle(cx, cy, R) for _ in range(PARTICLE_COUNT)]

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _tick(self):
        self._pulse = (self._pulse + PULSE_SPEED)  % (2 * math.pi)
        self._wave  = (self._wave  + 0.055)        % (2 * math.pi)
        self._wave2 = (self._wave2 + 0.038)        % (2 * math.pi)
        self._angle = (self._angle + 0.7)          % 360
        self._t    += 0.016

        for p in self._particles:
            p.update(self._state, self._t)

        self.update()

    def _state_colors(self):
        s = self._state
        if s == self.LISTENING:
            return (QColor(30,160,255), QColor(20,130,230,110),
                    QColor(0,170,255,45), QColor(70,190,255))
        elif s == self.PROCESSING:
            return (QColor(0,230,255), QColor(0,190,230,110),
                    QColor(0,210,255,50), QColor(0,240,255))
        elif s == self.SPEAKING:
            return (QColor(90,200,255), QColor(50,160,245,120),
                    QColor(60,180,255,55), QColor(110,220,255))
        else:
            return (QColor(26,130,240), QColor(18,100,200,90),
                    QColor(15,90,200,30), QColor(50,150,230))

    @staticmethod
    def _ca(v: int) -> int:
        """Clamp alpha to valid 0-255 range."""
        return max(0, min(255, v))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h   = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        R      = min(cx, cy) * 0.82

        pulse  = math.sin(self._pulse)
        pulse2 = math.sin(self._pulse * 1.618)
        pulse3 = math.sin(self._pulse * 2.414)

        c_part, c_conn, c_glow, c_ring = self._state_colors()

        glow_alpha = self._ca(int(30 + 25 * abs(pulse) + 10 * abs(pulse2)))
        bg_grad = QRadialGradient(cx, cy, R * 0.95)
        glow_in = QColor(c_glow); glow_in.setAlpha(glow_alpha)
        bg_grad.setColorAt(0.0, glow_in)
        bg_grad.setColorAt(0.45, QColor(c_glow.red(), c_glow.green(), c_glow.blue(), self._ca(glow_alpha // 3)))
        bg_grad.setColorAt(1.0,  QColor(0,0,0,0))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), R * 1.1, R * 1.1)

        projected = []
        for p in self._particles:
            px, py, scale, depth = p.project(cx, cy)
            projected.append((px, py, scale, depth, p))
        projected.sort(key=lambda x: x[2])

        n = len(projected)
        for i in range(n):
            ax, ay, sa, da, pa = projected[i]
            for j in range(i + 1, n):
                bx, by, sb, db, pb = projected[j]
                dist = math.hypot(ax - bx, ay - by)
                if dist < CONNECTION_DIST:
                    strength = 1.0 - dist / CONNECTION_DIST
                    depth_avg = (da + db) / 2
                    idle_mult = 1.0 if self._state != self.IDLE else 0.85
                    alpha = int(200 * strength * depth_avg * idle_mult)
                    pulse_boost = int(30 * abs(pulse2) * strength)
                    alpha = self._ca(alpha + pulse_boost)
                    lc = QColor(c_conn); lc.setAlpha(alpha)
                    pen = QPen(lc, max(0.5, strength * 1.6))
                    painter.setPen(pen)
                    painter.drawLine(QPointF(ax, ay), QPointF(bx, by))

        painter.setPen(Qt.NoPen)
        for px, py, scale, depth, p in projected:
            if self._state == self.IDLE:
                base_alpha = int(max(80, 240 * depth * p.alpha))
            else:
                base_alpha = int(230 * depth * p.alpha)
            pulse_ind = abs(math.sin(self._pulse + p._osc_phase))
            base_alpha = self._ca(int(base_alpha * (0.75 + 0.25 * pulse_ind)))
            sz = p.size * max(0.6, scale * 0.012)
            sz = max(1.4, min(sz, 5.5))
            g = QRadialGradient(px, py, sz * 3.5)
            gc = QColor(c_part); gc.setAlpha(self._ca(int(base_alpha * 0.40)))
            g.setColorAt(0.0, gc); g.setColorAt(1.0, QColor(0,0,0,0))
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(px, py), sz * 3.5, sz * 3.5)
            pc = QColor(c_part); pc.setAlpha(base_alpha)
            painter.setBrush(QBrush(pc))
            painter.drawEllipse(QPointF(px, py), sz, sz)

        n_rings = 4
        for i in range(n_rings):
            progress = ((self._pulse / (2 * math.pi)) + i / n_rings) % 1.0
            ring_r   = R * 0.18 + progress * R * 0.72
            if self._state == self.IDLE:
                alpha = self._ca(int(max(40, 130 * (1.0 - progress) * (0.6 + 0.4 * abs(pulse)))))
            else:
                alpha = self._ca(int(130 * (1.0 - progress) * (0.5 + 0.5 * abs(pulse))))
            rc = QColor(c_ring); rc.setAlpha(alpha)
            pen = QPen(rc, 0.9)
            painter.setPen(pen); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        arc_r = R * 0.88
        arc_rect = QRect(int(cx-arc_r), int(cy-arc_r), int(arc_r*2), int(arc_r*2))
        dim_c = QColor(c_ring); dim_c.setAlpha(60)
        dim_pen = QPen(dim_c, 1)
        painter.setPen(dim_pen); painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), arc_r, arc_r)
        span = 80 if self._state == self.IDLE else 110
        bright_pen = QPen(QColor(c_ring), 2); bright_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bright_pen)
        painter.drawArc(arc_rect, int(-self._angle * 16), span * 16)
        arc_r2 = R * 0.75
        arc_rect2 = QRect(int(cx-arc_r2), int(cy-arc_r2), int(arc_r2*2), int(arc_r2*2))
        arc2_c = QColor(c_ring); arc2_c.setAlpha(80 if self._state == self.IDLE else 140)
        arc2_pen = QPen(arc2_c, 1); arc2_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc2_pen)
        painter.drawArc(arc_rect2, int(self._angle * 12 * 16), 45 * 16)

        core_base = R * 0.11
        core_osc  = (core_base * 0.05 * abs(pulse) +
                     core_base * 0.03 * abs(pulse2) +
                     core_base * 0.02 * abs(pulse3))
        core_r = core_base + core_osc
        core_g = QRadialGradient(cx, cy, core_r * 2.5)
        bright_alpha = self._ca(int(220 + 35 * abs(pulse)))
        core_bright = QColor(c_ring); core_bright.setAlpha(bright_alpha)
        core_mid    = QColor(c_part); core_mid.setAlpha(self._ca(int(140 + 40 * abs(pulse2))))
        core_edge   = QColor(c_part); core_edge.setAlpha(self._ca(int(25 + 15 * abs(pulse3))))
        core_g.setColorAt(0.0, core_bright)
        core_g.setColorAt(0.4, core_mid)
        core_g.setColorAt(1.0, core_edge)
        painter.setBrush(QBrush(core_g)); painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), core_r * 2.5, core_r * 2.5)
        solid_g = QRadialGradient(cx, cy, core_r)
        solid_g.setColorAt(0.0, QColor(255,255,255,240))
        solid_g.setColorAt(0.5, core_bright)
        solid_g.setColorAt(1.0, core_mid)
        painter.setBrush(QBrush(solid_g))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        n_bars   = 48
        bar_base = R * 0.52
        bar_max  = R * 0.16
        for i in range(n_bars):
            ang   = math.radians(i * (360 / n_bars))
            phase = i * (2 * math.pi / n_bars)
            if self._state == self.SPEAKING:
                hb = bar_max * (0.25 + 0.75 * abs(math.sin(self._wave * 3.5 + phase)))
                bar_alpha = 180
            elif self._state == self.PROCESSING:
                hb = bar_max * (0.30 + 0.70 * abs(math.sin(self._wave * 5.5 + phase * 2)))
                bar_alpha = 200
            elif self._state == self.LISTENING:
                hb = bar_max * (0.15 + 0.55 * abs(math.sin(self._wave * 2.5 + phase)))
                bar_alpha = 150
            else:
                hb = bar_max * (0.18 + 0.32 * abs(
                    math.sin(self._wave * 1.5 + phase) * 0.6 +
                    math.sin(self._wave2 * 2.3 + phase * 0.7) * 0.4
                ))
                bar_alpha = 110
            x1 = cx + bar_base * math.cos(ang)
            y1 = cy + bar_base * math.sin(ang)
            x2 = cx + (bar_base + hb) * math.cos(ang)
            y2 = cy + (bar_base + hb) * math.sin(ang)
            ba = int(bar_alpha * (hb / bar_max))
            bc = QColor(c_ring); bc.setAlpha(max(15, ba))
            bpen = QPen(bc, 1.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(bpen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════════
# OVERLAY WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class OverlayWindow(QWidget):
    """Janela transparente sempre-no-topo que desenha o cursor de gestos."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if AG_OK:
            sw, sh = pyautogui.size()
        else:
            sw, sh = 1920, 1080
        self.setGeometry(0, 0, sw, sh)

        self.cx          = 0
        self.cy          = 0
        self.radius      = 0
        self.target_rect = None
        self.dwell_time  = 0.0
        self._visible    = False

    @Slot(int, int, int, object, float)
    def do_update(self, cx, cy, radius, target_rect, dwell_time):
        self.cx          = cx
        self.cy          = cy
        self.radius      = radius
        self.target_rect = target_rect
        self.dwell_time  = dwell_time
        self.update()

    def set_overlay_visible(self, visible: bool):
        self._visible = visible
        if visible:
            self.show()
        else:
            self.hide()

    def paintEvent(self, event):
        if not self._visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.target_rect:
            tx, ty, tr = self.target_rect
            tr = tr + 10
            pen = QPen(QColor(255, 255, 255, 180), 2)
            painter.setPen(pen)
            painter.drawEllipse(tx - tr, ty - tr, tr * 2, tr * 2)
            painter.drawLine(tx - tr - 5, ty, tx - tr + 5, ty)
            painter.drawLine(tx + tr - 5, ty, tx + tr + 5, ty)
            painter.drawLine(tx, ty - tr - 5, tx, ty - tr + 5)
            painter.drawLine(tx, ty + tr - 5, tx, ty + tr + 5)
            if 0 < self.dwell_time <= 1.0:
                arc_len = int(min(1.0, self.dwell_time) * 360 * 16)
                pen = QPen(QColor(255, 255, 255, 255), 4)
                painter.setPen(pen)
                painter.drawArc(tx-tr+4, ty-tr+4, (tr-4)*2, (tr-4)*2, 90*16, -arc_len)
        else:
            pen = QPen(QColor(255, 255, 255, 255), 3)
            painter.setPen(pen)
            painter.drawEllipse(self.cx-3, self.cy-3, 6, 6)
            pen = QPen(QColor(255, 255, 255, 100), 1)
            painter.setPen(pen)
            painter.drawLine(self.cx-10, self.cy, self.cx+10, self.cy)
            painter.drawLine(self.cx, self.cy-10, self.cx, self.cy+10)
            if 0 < self.dwell_time <= 1.0:
                arc_len = int(min(1.0, self.dwell_time) * 360 * 16)
                pen = QPen(QColor(255, 255, 255, 255), 3)
                painter.setPen(pen)
                painter.drawArc(self.cx-15, self.cy-15, 30, 30, 90*16, -arc_len)


# ═══════════════════════════════════════════════════════════════════════════════
# UI TARGET SCANNER
# ═══════════════════════════════════════════════════════════════════════════════
class UITargetScanner:
    """Varre elementos de UI via uiautomation em thread separada."""

    def __init__(self):
        self.running          = False
        self.current_pos      = None
        self.suggested_target = None
        self.lock             = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._scan_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def set_pos(self, x, y):
        with self.lock:
            self.current_pos = (x, y)

    def get_target(self):
        with self.lock:
            return self.suggested_target

    def _scan_loop(self):
        while self.running:
            pos = None
            with self.lock:
                pos = self.current_pos
            if pos and AUTO_OK:
                target = self._find_target_in_radius(pos[0], pos[1], radius=80)
                with self.lock:
                    self.suggested_target = target
            time.sleep(0.05)

    def _find_target_in_radius(self, x, y, radius=80):
        try:
            elem = auto.ControlFromPoint(x, y)
            if not elem:
                return None

            parent = elem
            for _ in range(2):
                p = parent.GetParentControl()
                if p: parent = p

            best_target = None
            min_dist    = radius

            def walk(ctrl, depth=0):
                nonlocal best_target, min_dist
                if depth > 4: return
                rect = ctrl.BoundingRectangle
                if rect.width() <= 0 or rect.height() <= 0: return
                if rect.width() <= 500 and rect.height() <= 500:
                    if not (rect.right < x-radius or rect.left > x+radius or
                            rect.bottom < y-radius or rect.top > y+radius):
                        cx2 = (rect.left + rect.right)  // 2
                        cy2 = (rect.top  + rect.bottom) // 2
                        dist = math.hypot(cx2 - x, cy2 - y)
                        clickable = ctrl.ControlType in [
                            auto.ControlType.ButtonControl,
                            auto.ControlType.MenuItemControl,
                            auto.ControlType.ListItemControl,
                            auto.ControlType.HyperlinkControl,
                            auto.ControlType.CheckBoxControl,
                            auto.ControlType.RadioButtonControl,
                            auto.ControlType.TabItemControl,
                        ] or ctrl.IsKeyboardFocusable
                        if dist <= min_dist and clickable:
                            min_dist = dist
                            tr = max(rect.width(), rect.height()) // 2 + 5
                            best_target = (cx2, cy2, tr)
                child = ctrl.GetFirstChildControl()
                while child:
                    walk(child, depth + 1)
                    child = child.GetNextSiblingControl()

            walk(parent)
            return best_target
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# GESTURE ENGINE v8
# ═══════════════════════════════════════════════════════════════════════════════
class GestureEngine:
    """Motor de gestos avançado com suporte a 2 mãos e 12 classificações."""

    TIPS = [4, 8, 12, 16, 20]

    GESTURE_LABELS = {
        "PUNHO":        "✊  PUNHO",
        "PALMA":        "✋  PALMA",
        "SÓ_POLEGAR":   "👍  POLEGAR",
        "SÓ_INDICADOR": "☝️  INDICADOR",
        "SÓ_MINIMO":    "🤙  MÍNIMO",
        "2_DEDOS":      "✌️  2 DEDOS",
        "3_DEDOS":      "🤟  3 DEDOS",
        "4_DEDOS":      "🖖  4 DEDOS",
        "L_SHAPE":      "L   L-SHAPE",
        "L_MINIMO":     "🤘  L+MÍNIMO",
        "OUTRO":        "—   OUTRO",
        "NENHUM":       "—   NENHUM",
    }

    def __init__(self):
        self.cap = None
        self.ok = CV2_OK
        if not self.ok:
            return

        self._mp_hands = mp.solutions.hands
        self._draw     = mp.solutions.drawing_utils

        self.hands_solver = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=0,              # modelo leve → menor uso de CPU
            min_detection_confidence=0.65,
            min_tracking_confidence=0.60,
        )

    def _fingers(self, lm, label: str) -> list[int]:
        if label == 'Right':
            thumb = 1 if lm[4].x < lm[3].x else 0
        else:
            thumb = 1 if lm[4].x > lm[3].x else 0
        f = [thumb]
        for t in self.TIPS[1:]:
            f.append(1 if lm[t].y < lm[t - 2].y else 0)
        return f

    def _classify(self, lm, label: str) -> dict:
        ff = self._fingers(lm, label)
        if   ff == [0,0,0,0,0]: g = "PUNHO"
        elif ff == [1,1,1,1,1]: g = "PALMA"
        elif ff == [1,0,0,0,0]: g = "SÓ_POLEGAR"
        elif ff == [0,1,0,0,0]: g = "SÓ_INDICADOR"
        elif ff == [0,0,0,0,1]: g = "SÓ_MINIMO"
        elif ff == [0,1,1,0,0]: g = "2_DEDOS"
        elif ff == [0,1,1,1,0]: g = "3_DEDOS"
        elif ff == [0,1,1,1,1]: g = "4_DEDOS"
        elif ff == [1,1,0,0,0]: g = "L_SHAPE"
        elif ff == [1,1,0,0,1]: g = "L_MINIMO"
        else:                   g = "OUTRO"
        return dict(
            g=g, ff=ff,
            ix=lm[8].x, iy=lm[8].y,
            wx=lm[0].x, wy=lm[0].y,
            label=label,
        )

    def start(self) -> bool:
        if not self.ok:
            return False
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def read(self):
        if not self.ok or not self.cap:
            return None, []

        ret, frame = self.cap.read()
        if not ret:
            return None, []

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Otimização: evita cópia interna do MediaPipe
        rgb.flags.writeable = False
        res = self.hands_solver.process(rgb)
        rgb.flags.writeable = True

        hands_data = []
        if res.multi_hand_landmarks and res.multi_handedness:
            for hlm, hness in zip(res.multi_hand_landmarks, res.multi_handedness):
                label = hness.classification[0].label
                data  = self._classify(hlm.landmark, label)
                col   = (0, 255, 128) if label == 'Right' else (255, 128, 0)
                self._draw.draw_landmarks(
                    frame, hlm, self._mp_hands.HAND_CONNECTIONS,
                    self._draw.DrawingSpec(color=col, thickness=2, circle_radius=3),
                    self._draw.DrawingSpec(color=(col[0]//2, col[1]//2, col[2]//2), thickness=1),
                )
                lx = int(hlm.landmark[0].x * frame.shape[1])
                ly = int(hlm.landmark[0].y * frame.shape[0]) - 15
                cv2.putText(frame, f"{label}: {data['g']}",
                            (max(0, lx-40), max(0, ly)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
                hands_data.append(data)

        return frame, hands_data


# ═══════════════════════════════════════════════════════════════════════════════
# CURSOR CONTROLLER v8
# ═══════════════════════════════════════════════════════════════════════════════
class CursorController:
    def __init__(self, ui_ref, scanner: UITargetScanner):
        self._ui      = ui_ref
        self._scanner = scanner

        if AG_OK:
            self._sw, self._sh = pyautogui.size()
        else:
            self._sw, self._sh = 1920, 1080

        self._smooth_pos   = None
        self._ma_buffers   = {}
        self._gest_buf     = {'Left': [], 'Right': []}
        self._active_g     = {'Left': "NENHUM", 'Right': "NENHUM"}

        self._ignoring    = False
        self._last_toggle = 0.0
        self._dragging    = False
        self._alt_on      = False
        self._ctrl_on     = False
        self._vol_mode    = False
        self._scroll_mode = False
        self._scroll_cd   = 0.0

        self._last_pos  = None
        self._last_time = time.time()
        self._speed     = 0.0

        self._locked_target      = None
        self._lock_time          = 0.0
        self._hover_target       = None

        self._confirming_click   = False
        self._confirm_start      = 0.0
        self._confirm_target_pos = None

        self._cooldowns = {}
        self._dpr       = 1.0

    def _ma(self, key, val, size=5):
        if key not in self._ma_buffers:
            self._ma_buffers[key] = []
        b = self._ma_buffers[key]
        b.append(val)
        if len(b) > size:
            b.pop(0)
        return sum(b) / len(b)

    def _last_y_store(self):
        if not hasattr(self, '_ly_store'):
            self._ly_store = {}
        return self._ly_store

    def _get_dy(self, key, curr_y):
        store = self._last_y_store()
        if key not in store:
            store[key] = curr_y
            return 0
        dy = store[key] - curr_y
        store[key] = curr_y
        return dy

    def _check_cd(self, key, delay=0.8) -> bool:
        now = time.time()
        if now - self._cooldowns.get(key, 0) > delay:
            self._cooldowns[key] = now
            return True
        return False

    def _get_active(self, label, detected_g) -> str:
        buf = self._gest_buf[label]
        buf.append(detected_g)
        if len(buf) > 5:
            buf.pop(0)
        if len(buf) == 5 and len(set(buf)) == 1:
            return buf[0]
        return self._active_g[label]

    def _mv(self, nx, ny):
        MX_L, MX_R = 0.15, 0.85
        MY_T, MY_B = 0.10, 0.65
        tx = int(max(0., min(1., (nx - MX_L) / (MX_R - MX_L))) * self._sw)
        ty = int(max(0., min(1., (ny - MY_T) / (MY_B - MY_T))) * self._sh)
        fx = self._ma('cx', tx)
        fy = self._ma('cy', ty)
        if self._smooth_pos is None:
            self._smooth_pos = (fx, fy)
        cx, cy = self._smooth_pos
        S = 0.35
        nx2 = max(0, min(self._sw - 1, int(cx + (fx - cx) * S * 2)))
        ny2 = max(0, min(self._sh - 1, int(cy + (fy - cy) * S * 2)))
        self._smooth_pos = (nx2, ny2)
        return nx2, ny2

    def clear_inputs(self, forced=False):
        changed = False
        if self._dragging:
            if AG_OK: pyautogui.mouseUp(button='left', _pause=False)
            self._dragging = False
            changed = True
        if self._alt_on:
            if AG_OK: pyautogui.keyUp('alt', _pause=False)
            self._alt_on = False
            changed = True
        if self._ctrl_on:
            if AG_OK: pyautogui.keyUp('ctrl', _pause=False)
            self._ctrl_on = False
            changed = True
        if (changed or forced) and self._check_cd('reset_log', 1.0):
            self._ui.add_log("🧹 Inputs resetados", "alerta")

    def process(self, hands: list[dict]):
        active = {'Left': "NENHUM", 'Right': "NENHUM"}
        for h in hands:
            label = h['label']
            active[label] = self._get_active(label, h['g'])
        self._active_g = active

        r_g = active['Right']
        l_g = active['Left']
        r_hand = next((h for h in hands if h['label'] == 'Right'), None)
        l_hand = next((h for h in hands if h['label'] == 'Left'), None)

        self._ui.sig_gesture_adv.emit(r_g, l_g)

        if r_g == "PUNHO" or l_g == "PUNHO":
            self.clear_inputs(forced=True)
            if r_g == "PUNHO" and self._check_cd('fist_cancel', 1.5):
                self._ui.add_log("✊ PUNHO → Cancelar / Reset", "gesto")
                speak("Comando cancelado, senhor.", self._ui)

        if l_g == "3_DEDOS":
            if not self._vol_mode:
                self._vol_mode = True
                self._ui.add_log("🔊 Modo volume ativo (3 dedos esq.)", "alerta")
            if r_hand:
                rg_raw = r_hand['g']
                if rg_raw == "SÓ_INDICADOR" and self._check_cd('vol_up', 0.15):
                    if AG_OK: pyautogui.press('volumeup')
                    self._ui.add_log("🔊 Volume ▲", "gesto")
                elif rg_raw == "2_DEDOS" and self._check_cd('vol_dn', 0.15):
                    if AG_OK: pyautogui.press('volumedown')
                    self._ui.add_log("🔉 Volume ▼", "gesto")
            self._ui.sig_overlay.emit(0, 0, 0, None, 0.0)
            return
        else:
            if self._vol_mode:
                self._vol_mode = False
                self._ui.add_log("🔊 Modo volume desativado", "alerta")

        if r_g == "PALMA" and r_hand:
            now = time.time()
            if now - self._last_toggle > 2.0:
                self._ignoring = not self._ignoring
                self._last_toggle = now
                estado = "DESATIVADO" if self._ignoring else "ATIVADO"
                self._ui.add_log(f"✋ Controle de cursor {estado}", "alerta")
                speak(f"Controle de cursor {'desativado' if self._ignoring else 'ativado'}, senhor.", self._ui)

        if self._ignoring:
            self._ui.sig_overlay.emit(0, 0, 0, None, 0.0)
            return

        if r_hand:
            if r_g == "4_DEDOS":
                if not self._scroll_mode:
                    self._scroll_mode = True
                    self._ui.add_log("📜 Modo scroll (4 dedos dir.)", "alerta")
                    self._last_y_store()['scroll'] = r_hand['wy']
                dy = self._get_dy('scroll', r_hand['wy'])
                now = time.time()
                if abs(dy) > 0.015 and now - self._scroll_cd > 0.08:
                    clicks = int(dy * 10000)
                    if abs(clicks) > 0 and AG_OK:
                        pyautogui.scroll(clicks)
                    self._scroll_cd = now
                self._ui.sig_overlay.emit(0, 0, 0, None, 0.0)
                return
            else:
                if self._scroll_mode:
                    self._scroll_mode = False
                    self._ui.add_log("📜 Scroll desativado", "alerta")

            if r_g in ("L_SHAPE", "2_DEDOS", "SÓ_INDICADOR"):
                is_hand_cursor = False
                if WIN32_OK:
                    try:
                        flags, hcursor, pt = win32gui.GetCursorInfo()
                        h_hand = win32gui.LoadCursor(0, win32con.IDC_HAND)
                        is_hand_cursor = (hcursor == h_hand)
                    except Exception:
                        pass

                x_raw, y_raw = self._mv(r_hand['ix'], r_hand['iy'])

                now = time.time()
                dt  = now - self._last_time
                if dt > 0 and self._last_pos:
                    dx  = x_raw - self._last_pos[0]
                    dy2 = y_raw - self._last_pos[1]
                    self._speed = math.hypot(dx, dy2) / dt
                self._last_time = now
                self._last_pos  = (x_raw, y_raw)

                if self._scanner:
                    self._scanner.set_pos(x_raw, y_raw)

                mode = "RAW" if (r_g == "2_DEDOS" or self._speed > 800) else "ASSIST"
                fx, fy = x_raw, y_raw
                intent_r    = 0
                target_rect = None

                if mode == "ASSIST":
                    intent_r = 60
                    target   = self._scanner.get_target() if self._scanner else None
                    if self._locked_target:
                        ltx, lty, _ = self._locked_target
                        if math.hypot(x_raw-ltx, y_raw-lty) > intent_r + 20:
                            self._locked_target = None
                        else:
                            target = self._locked_target
                    else:
                        if target:
                            tx, ty, tr = target
                            if math.hypot(x_raw-tx, y_raw-ty) <= intent_r:
                                self._locked_target = target
                                self._lock_time = now
                    if self._locked_target:
                        fx, fy = self._locked_target[0], self._locked_target[1]
                        target_rect = self._locked_target
                    elif is_hand_cursor:
                        target_rect = (x_raw, y_raw, 20)
                else:
                    self._locked_target = None

                if target_rect:
                    if self._hover_target:
                        dist = math.hypot(target_rect[0]-self._hover_target[0],
                                          target_rect[1]-self._hover_target[1])
                        if dist < 40:
                            target_rect = (self._hover_target[0], self._hover_target[1], target_rect[2])
                        else:
                            self._hover_target = (target_rect[0], target_rect[1])
                    else:
                        self._hover_target = (target_rect[0], target_rect[1])
                else:
                    self._hover_target = None

                dwell_time = 0.0
                if r_g == "SÓ_INDICADOR":
                    if not self._confirming_click:
                        self._confirming_click   = True
                        self._confirm_start      = now
                        self._confirm_target_pos = (fx, fy)
                    else:
                        dist_raw = math.hypot(x_raw - self._confirm_target_pos[0],
                                              y_raw - self._confirm_target_pos[1])
                        if dist_raw < 70:
                            fx, fy     = self._confirm_target_pos
                            dwell_time = now - self._confirm_start
                            if dwell_time >= 1.0:
                                if AG_OK:
                                    pyautogui.click(button='left', _pause=False)
                                self._ui.add_log("🤌 Click confirmado (dwell)", "gesto")
                                self._confirming_click = False
                                self._confirm_start    = now + 1.0
                                dwell_time             = 0.0
                        else:
                            self._confirming_click   = True
                            self._confirm_start      = now
                            self._confirm_target_pos = (fx, fy)
                else:
                    self._confirming_click = False
                    self._confirm_start    = 0

                scx = int(x_raw / self._dpr)
                scy = int(y_raw / self._dpr)
                starget = (int(target_rect[0]/self._dpr),
                           int(target_rect[1]/self._dpr),
                           int(target_rect[2]/self._dpr)) if target_rect else None
                self._ui.sig_overlay.emit(scx, scy, int(intent_r/self._dpr), starget, dwell_time)

                if AG_OK:
                    pyautogui.moveTo(fx, fy, _pause=False)

                if r_g == "2_DEDOS":
                    if not self._dragging:
                        if AG_OK: pyautogui.mouseDown(button='left', _pause=False)
                        self._dragging = True
                        self._ui.add_log("✊ Arrastar iniciado", "gesto")
                elif self._dragging:
                    if AG_OK: pyautogui.mouseUp(button='left', _pause=False)
                    self._dragging = False

            else:
                self._ui.sig_overlay.emit(0, 0, 0, None, 0.0)

        if l_hand:
            if l_g == "L_SHAPE":
                if not self._alt_on:
                    if AG_OK: pyautogui.keyDown('alt', _pause=False)
                    self._alt_on = True
                    self._ui.add_log("⌨️ ALT pressionado", "alerta")
            elif l_g == "L_MINIMO" and self._alt_on:
                if self._check_cd('tab', 0.8):
                    if AG_OK: pyautogui.press('tab', _pause=False)
                    self._ui.add_log("⌨️ ALT+TAB", "alerta")
            elif l_g not in ("L_SHAPE", "L_MINIMO") and self._alt_on:
                if AG_OK: pyautogui.keyUp('alt', _pause=False)
                self._alt_on = False
                self._ui.add_log("⌨️ ALT liberado", "alerta")

            if l_g == "4_DEDOS" and self._check_cd('desk', 1.0):
                if AG_OK: pyautogui.hotkey('win', 'd')
                self._ui.add_log("🖥  Mostrar desktop (Win+D)", "alerta")

        if l_g == "PALMA" and l_hand and self._check_cd('voice_act', 2.5):
            self._ui.add_log("✋ Palma esq. → Ativando escuta", "gesto")
            speak("Estou ouvindo, senhor.", self._ui)
            self._ui.sig_state.emit("listening")


# ═══════════════════════════════════════════════════════════════════════════════
# VOICE ENGINE  —  ElevenLabs  (substitui edge_tts)
# ═══════════════════════════════════════════════════════════════════════════════
CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_eleven_cache"
CACHE_DIR.mkdir(exist_ok=True)

PRECACHE_PHRASES = [
    "Sim, senhor.", "Claro, senhor.", "Certamente, senhor.", "Agora mesmo, senhor.",
    "Todos os sistemas estão operacionais, senhor.", "Como desejar, senhor.", "Entendido, senhor.",
    "Câmera ativada. Controle por gestos está online, senhor.", "Câmera desativada, senhor.",
    "Abrindo o Google, senhor.", "Abrindo o YouTube, senhor.", "Abrindo o Spotify, senhor.",
    "Abrindo o Discord, senhor.", "Abrindo o GitHub, senhor.", "Abrindo o WhatsApp, senhor.",
    "Abrindo a Netflix, senhor.", "Volume aumentado, senhor.", "Volume diminuído, senhor.",
    "Áudio silenciado, senhor.", "Captura de tela salva, senhor.",
    "Bloqueando a estação de trabalho, senhor.", "Desligando em cinco segundos, senhor.",
    "Reiniciando o sistema, senhor.", "Comando cancelado, senhor.",
    "Gesto confirmado, senhor.", "Estou ouvindo, senhor.",
    "Controle de cursor ativado, senhor.", "Controle de cursor desativado, senhor.",
    "JARVIS online. Todos os módulos carregados. Pronto para seus comandos, senhor.",
]

_voz_q       = queue.Queue()
_speak_ready = threading.Event()


def _cache_key(text: str) -> str:
    key = f"{ELEVENLABS_VOICE_ID}:{ELEVENLABS_MODEL}:{text}"
    return hashlib.md5(key.encode()).hexdigest()


def _cache_path(text: str) -> Path:
    return CACHE_DIR / f"{_cache_key(text)}.mp3"


def _generate_eleven(text: str) -> bytes | None:
    """Chama a API ElevenLabs e retorna bytes MP3."""
    if not ELEVEN_OK or _eleven_client is None:
        return None
    try:
        audio = _eleven_client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id=ELEVENLABS_MODEL,
            voice_settings=VoiceSettings(
                stability=ELEVENLABS_SETTINGS["stability"],
                similarity_boost=ELEVENLABS_SETTINGS["similarity_boost"],
                style=ELEVENLABS_SETTINGS["style"],
                use_speaker_boost=ELEVENLABS_SETTINGS["use_speaker_boost"],
            ),
        )
        # A API retorna um gerador; converte para bytes
        if hasattr(audio, '__iter__'):
            return b"".join(audio)
        return audio
    except Exception as e:
        print(f"[ElevenLabs] Erro na API: {e}")
        return None


def _ensure_cached(text: str) -> Path | None:
    """Garante que o áudio está em disco. Gera via API se necessário."""
    path = _cache_path(text)
    if path.exists() and path.stat().st_size > 0:
        return path
    audio_bytes = _generate_eleven(text)
    if audio_bytes:
        path.write_bytes(audio_bytes)
        return path
    return None


def _play_audio(path: Path):
    """Reproduz MP3 via pygame."""
    if not PG_OK or not path or not path.exists():
        return
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except Exception as e:
        print(f"[Áudio] Erro ao reproduzir: {e}")


_pyttsx3_engine = None

def _pyttsx3_fallback(text: str):
    """TTS local — usado quando ElevenLabs não está disponível."""
    global _pyttsx3_engine
    try:
        import pyttsx3
        if _pyttsx3_engine is None:
            _pyttsx3_engine = pyttsx3.init()
            _pyttsx3_engine.setProperty('rate', 160)
            # Tenta encontrar voz em português
            for v in _pyttsx3_engine.getProperty('voices'):
                nome = v.name.lower()
                if 'portug' in nome or 'brazil' in nome or 'pt' in v.id.lower():
                    _pyttsx3_engine.setProperty('voice', v.id)
                    break
        _pyttsx3_engine.say(text)
        _pyttsx3_engine.runAndWait()
    except Exception as e:
        print(f"[TTS Fallback] Falha no TTS local: {e}")


def _voz_worker():
    """Worker de fila: processa textos em ordem."""
    while True:
        text = _voz_q.get()
        try:
            if ELEVEN_OK and PG_OK:
                path = _ensure_cached(text)
                if path:
                    _play_audio(path)
                else:
                    # ElevenLabs falhou — tenta fallback
                    _pyttsx3_fallback(text)
            else:
                _pyttsx3_fallback(text)
        except Exception:
            pass
        _voz_q.task_done()


def _precache_worker():
    """Pré-gera cache das frases comuns em background."""
    for phrase in PRECACHE_PHRASES:
        _ensure_cached(phrase)
        time.sleep(0.3)   # evita rate-limit
    _speak_ready.set()


# Inicia workers ao carregar o módulo
threading.Thread(target=_voz_worker,      daemon=True).start()
threading.Thread(target=_precache_worker, daemon=True).start()


def speak(text: str, ui=None):
    """Função pública — enfileira texto para síntese e reprodução."""
    if ui:
        ui.add_log(f"JARVIS › {text}", "jarvis")
    _voz_q.put(text)


# ── Mapeamentos de resposta ───────────────────────────────────────────────────
RESPOSTAS = {
    "jarvis": "Sim, senhor.", "sim": "Claro, senhor.", "ok": "Agora mesmo, senhor.",
    "obrigado": "É um prazer, senhor.", "google": "Abrindo o Google, senhor.",
    "youtube": "Abrindo o YouTube, senhor.", "spotify": "Abrindo o Spotify, senhor.",
    "discord": "Abrindo o Discord, senhor.", "whatsapp": "Abrindo o WhatsApp, senhor.",
    "netflix": "Abrindo a Netflix, senhor.", "github": "Abrindo o GitHub, senhor.",
    "chatgpt": "Abrindo o ChatGPT, senhor.", "gmail": "Abrindo o Gmail, senhor.",
    "status": "Buscando diagnóstico do sistema, senhor.",
    "screenshot": "Captura de tela salva na pasta Imagens, senhor.",
    "bloqueia": "Bloqueando a estação de trabalho, senhor.",
    "desliga": "Iniciando sequência de desligamento em cinco segundos, senhor.",
    "reinicia": "Reiniciando o sistema, senhor.",
    "sair": "Encerrando JARVIS. Bom dia, senhor.",
}


def jarvis_response(q: str) -> str:
    q = q.lower().strip()
    for key, resp in RESPOSTAS.items():
        if key in q and resp:
            return resp
    return random.choice([
        "Entendido, senhor.", "Processando sua solicitação, senhor.",
        "Comando recebido, senhor.", "Anotado, senhor.",
        "Estou nessa, senhor.", "Afirmativo, senhor.", "Considere feito, senhor.",
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════════════════════
def sys_info() -> dict:
    try:
        cpu  = psutil.cpu_percent(interval=0.2) if PS_OK else 0
        ram  = psutil.virtual_memory()          if PS_OK else None
        disk = psutil.disk_usage('/')           if PS_OK else None
        bat  = psutil.sensors_battery()         if PS_OK else None
        host = socket.gethostname()
        ip   = socket.gethostbyname(host)
        return dict(
            cpu  = f"{cpu:.0f}%",
            ram  = f"{ram.percent:.0f}%"  if ram  else "N/A",
            disk = f"{disk.percent:.0f}%" if disk else "N/A",
            bat  = (f"{bat.percent:.0f}%{'⚡' if bat.power_plugged else ''}") if bat else "N/A",
            ip=ip, host=host,
        )
    except Exception:
        return {k: "?" for k in ["cpu", "ram", "disk", "bat", "ip", "host"]}


def vol_ctrl(d: str):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        dev   = AudioUtilities.GetSpeakers()
        iface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol   = cast(iface, POINTER(IAudioEndpointVolume))
        if d == 'up':
            vol.SetMasterVolumeLevel(min(vol.GetMasterVolumeLevel() + 2., 0.), None)
        elif d == 'dn':
            vol.SetMasterVolumeLevel(max(vol.GetMasterVolumeLevel() - 2., -65.25), None)
        elif d == 'mu':
            vol.SetMute(not vol.GetMute(), None)
    except Exception:
        if AG_OK:
            {'up': lambda: pyautogui.press('volumeup'),
             'dn': lambda: pyautogui.press('volumedown'),
             'mu': lambda: pyautogui.press('volumemute')}.get(d, lambda: None)()


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLER
# ═══════════════════════════════════════════════════════════════════════════════
SITES = {
    "youtube":  ("https://youtube.com",         "YouTube"),
    "google":   ("https://google.com",          "Google"),
    "github":   ("https://github.com",          "GitHub"),
    "chatgpt":  ("https://chat.openai.com",     "ChatGPT"),
    "gmail":    ("https://mail.google.com",     "Gmail"),
    "whatsapp": ("https://web.whatsapp.com",    "WhatsApp"),
    "netflix":  ("https://netflix.com",         "Netflix"),
    "twitch":   ("https://twitch.tv",           "Twitch"),
    "reddit":   ("https://reddit.com",          "Reddit"),
    "linkedin": ("https://linkedin.com",        "LinkedIn"),
}

MENU_ITEMS = [
    ("Google","google"), ("YouTube","youtube"), ("Spotify","spotify"),
    ("WhatsApp","whatsapp"), ("VS Code","vs code"), ("Status","status"),
    ("Discord","discord"), ("Hora","hora"), ("Screenshot","screenshot"), ("Sair","sair"),
]


def cmd(query: str, ui):
    q = query.lower().strip()
    if not q: return

    # ── Comandos de clima (integração com jarvis_clima.py) ────────────────────
    if CLIMA_OK and any(p in q for p in PALAVRAS_CLIMA):
        try:
            cmd_clima(q, ui, lambda txt: speak(txt, ui))
        except Exception as e:
            speak("Desculpe, senhor, houve um erro ao consultar os dados do clima.", ui)
            ui.add_log(f"❌ Erro no módulo de clima: {e}", "erro")
        return

    if "hora" in q or "que horas" in q:
        agora = datetime.datetime.now().strftime('%H:%M')
        speak(f"Agora são {agora}, senhor.", ui); return
    if "data" in q or "que dia" in q:
        DIAS_PT = {"Monday": "segunda-feira", "Tuesday": "terça-feira", "Wednesday": "quarta-feira",
                   "Thursday": "quinta-feira", "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo"}
        MESES_PT = {"January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril",
                    "May": "maio", "June": "junho", "July": "julho", "August": "agosto",
                    "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"}
        n = datetime.datetime.now()
        dia_sem = DIAS_PT.get(n.strftime('%A'), n.strftime('%A'))
        mes = MESES_PT.get(n.strftime('%B'), n.strftime('%B'))
        speak(f"Hoje é {dia_sem}, {n.day} de {mes} de {n.year}, senhor.", ui); return
    if "status" in q or "sistema" in q:
        i = sys_info()
        speak(f"CPU em {i['cpu']}, memória em {i['ram']}. Todos os sistemas operacionais, senhor.", ui)
        ui.update_stats(i); return
    if "desliga" in q:
        speak("Iniciando desligamento. Cinco segundos, senhor.", ui)
        time.sleep(5)
        if platform.system() == "Windows": os.system("shutdown /s /t 1")
        else: os.system("shutdown now")
        return
    if "reinicia" in q:
        speak("Reiniciando o sistema, senhor.", ui)
        if platform.system() == "Windows": os.system("shutdown /r /t 3")
        else: os.system("reboot")
        return
    if "bloqueia" in q or "trava" in q:
        speak("Bloqueando a estação de trabalho, senhor.", ui)
        try:
            if platform.system() == "Windows": ctypes.windll.user32.LockWorkStation()
            else: os.system("xdg-screensaver lock")
        except Exception: pass
        return
    if "volume" in q:
        if any(x in q for x in ["aumenta","sobe","mais","cima"]):
            vol_ctrl('up'); speak("Volume aumentado, senhor.", ui)
        elif any(x in q for x in ["diminui","baixa","menos"]):
            vol_ctrl('dn'); speak("Volume diminuído, senhor.", ui)
        elif any(x in q for x in ["muta","silencia","mudo"]):
            vol_ctrl('mu'); speak("Áudio silenciado, senhor.", ui)
        return
    for k, (url, name) in SITES.items():
        if k in q:
            frase = q.replace(k,"").replace("abre","").replace("pesquisa","").strip()
            full  = url
            if frase and k == "youtube":
                full = f"https://www.youtube.com/results?search_query={frase.replace(' ','+')}"
            elif frase and k == "google":
                full = f"https://www.google.com/search?q={frase.replace(' ','+')}"
            if WB_OK: wb.open(full)
            speak(f"Abrindo o {name}, senhor.", ui); return
    if "spotify" in q:
        try:
            if platform.system() == "Windows": os.startfile("spotify:")
            else: subprocess.Popen(["spotify"])
        except Exception:
            if WB_OK: wb.open("https://open.spotify.com")
        speak("Abrindo o Spotify, senhor.", ui); return

    if platform.system() == "Windows":
        local_apps = {
            "discord":        os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
            "notepad":        "notepad.exe",
            "bloco de notas": "notepad.exe",
            "calculadora":    "calc.exe",
            "paint":          "mspaint.exe",
            "explorer":       "explorer.exe",
            "gerenciador":    "taskmgr.exe",
            "vs code":        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            "vscode":         os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        }
    else:
        local_apps = {
            "discord":        "discord",
            "notepad":        "gedit",
            "bloco de notas": "gedit",
            "calculadora":    "gnome-calculator",
            "paint":          "kolourpaint",
            "explorer":       "nautilus",
            "gerenciador":    "gnome-system-monitor",
            "vs code":        "code",
            "vscode":         "code",
        }
    for k, exe in local_apps.items():
        if k in q:
            try: subprocess.Popen([exe])
            except Exception: pass
            speak(f"Abrindo {k}, senhor.", ui); return

    if "screenshot" in q or "print" in q or "captura" in q:
        if AG_OK:
            try:
                p = os.path.join(Path.home(), "Pictures",
                    f"jarvis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                pyautogui.screenshot(p)
                speak("Captura de tela salva, senhor.", ui)
                ui.add_log(f"📸 {p}", "info")
            except Exception:
                speak("Não foi possível capturar a tela, senhor.", ui)
        return

    if "timer" in q or "alarme" in q:
        nums = [int(s) for s in q.split() if s.isdigit()]
        if nums:
            secs = nums[0] * 60 if "minuto" in q else nums[0]
            unidade = 'minutos' if 'minuto' in q else 'segundos'
            speak(f"Timer definido para {nums[0]} {unidade}, senhor.", ui)
            def _t(): time.sleep(secs); speak("Seu timer chegou ao fim, senhor.", ui)
            threading.Thread(target=_t, daemon=True).start()
        else:
            speak("Por favor, informe a duração do timer, senhor.", ui)
        return

    if "meu ip" in q:
        try: speak(f"Seu IP é {socket.gethostbyname(socket.gethostname())}, senhor.", ui)
        except Exception: speak("Não foi possível obter o IP, senhor.", ui)
        return

    if "sair" in q or "fechar jarvis" in q or "encerra" in q:
        speak("Encerrando JARVIS. Foi um prazer, senhor.", ui)
        time.sleep(2); QApplication.quit(); return

    speak(jarvis_response(q), ui)


# ═══════════════════════════════════════════════════════════════════════════════
# VOICE RECOGNITION
# ═══════════════════════════════════════════════════════════════════════════════
def listen_loop(ui):
    if not SR_OK:
        ui.add_log("SpeechRecognition não instalado.", "erro")
        return
    r = sr.Recognizer()
    r.energy_threshold         = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold          = 0.6
    ativo = False; t_ativo = 0; cooldown = 0.0
    ui.add_log("Microfone pronto. Diga 'JARVIS' para ativar.", "info")

    while True:
        try:
            if PG_OK and pygame.mixer.music.get_busy():
                ui.sig_state.emit("speaking"); time.sleep(0.1); continue
            else:
                ui.sig_state.emit("listening" if ativo else "idle")
            if time.time() < cooldown:
                time.sleep(0.1); continue
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.2)
                audio = r.listen(src, timeout=4, phrase_time_limit=8)
            q   = r.recognize_google(audio, language="pt-BR").lower()
            now = time.time()
            ui.add_log(f"YOU › {q}", "user")
            if "jarvis" in q:
                ativo = True; t_ativo = now
                ui.add_log("WAKE WORD", "alerta")
                ui.sig_state.emit("listening")
                speak("Sim, senhor.", ui); cooldown = now + 2.5; continue
            if ativo and (now - t_ativo < 15):
                ui.sig_state.emit("processing")
                # Verifica se é comando de clima (prioridade alta)
                if CLIMA_OK and any(p in q for p in PALAVRAS_CLIMA):
                    speak("Consultando o clima para você, senhor.", ui)
                    cooldown = now + 3.0
                    threading.Thread(target=cmd, args=(q, ui), daemon=True).start()
                else:
                    speak(jarvis_response(q), ui); cooldown = now + 2.0
                    threading.Thread(target=cmd, args=(q, ui), daemon=True).start()
                t_ativo = now
            else:
                ativo = False
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            pass
        except Exception:
            time.sleep(2)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class JarvisUI(QMainWindow):
    sig_log     = Signal(str, str)
    sig_volume  = Signal(int)
    sig_stats   = Signal(dict)
    sig_cam_img = Signal(object)
    sig_state   = Signal(str)

    sig_gesture_adv = Signal(str, str)
    sig_overlay     = Signal(int, int, int, object, float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S  ·  v8.1  [ElevenLabs]")
        self.resize(1120, 720)
        self.setMinimumSize(900, 580)
        self.setStyleSheet(GLOBAL_QSS)

        self.menu_idx = 0
        self._cam_on  = False

        self._engine  = GestureEngine()
        self._scanner = UITargetScanner()
        self._overlay = OverlayWindow()
        self._ctrl    = None

        self._fps_count = 0
        self._fps_time  = time.time()

        self._build_ui()
        self._connect_signals()

        self._ctrl = CursorController(self, self._scanner)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._clock_tick)
        self._clock_timer.start(1000)

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._stats_tick)
        self._stats_timer.start(8000)

        threading.Thread(target=listen_loop, args=(self,), daemon=True).start()
        self._scanner.start()

    def _connect_signals(self):
        self.sig_log.connect(self._append_log)
        self.sig_volume.connect(self._vol_bar.setValue)
        self.sig_stats.connect(self._apply_stats)
        self.sig_cam_img.connect(self._update_cam_pixmap)
        self.sig_state.connect(self._on_state)
        self.sig_gesture_adv.connect(self._on_gesture_adv)
        self.sig_overlay.connect(self._overlay.do_update)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        main.addWidget(self._build_sidebar(), 0)
        main.addWidget(self._build_stage(),   1)

    def _build_sidebar(self):
        panel = QWidget()
        panel.setFixedWidth(275)
        panel.setStyleSheet(f"background:{DS.BG1}; border-right:1px solid {DS.BORDER_BLUE};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        hdr = QWidget(); hdr.setFixedHeight(52)
        hdr.setStyleSheet(f"background:{DS.BG0}; border-bottom:1px solid {DS.BORDER_BLUE};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16, 0, 16, 0)
        logo = QLabel("J.A.R.V.I.S")
        logo.setStyleSheet(f"color:{DS.BLUE_BRIGHT}; font-family:{DS.FONT_DISPLAY}; font-size:13px; font-weight:700; letter-spacing:3px; background:transparent;")
        hl.addWidget(logo); hl.addStretch()
        ver = QLabel("v8.1 · ElevenLabs")
        ver.setStyleSheet(f"color:{DS.T3}; font-size:9px; background:transparent;")
        hl.addWidget(ver)
        layout.addWidget(hdr)

        # ── Status ElevenLabs ─────────────────────────────────────────────────
        eleven_w = QWidget(); eleven_w.setStyleSheet("background:transparent;")
        eleven_l = QHBoxLayout(eleven_w)
        eleven_l.setContentsMargins(12, 6, 12, 2); eleven_l.setSpacing(6)
        eleven_icon = QLabel("🔊")
        eleven_icon.setStyleSheet("background:transparent; font-size:11px;")
        eleven_l.addWidget(eleven_icon)
        eleven_status_txt = "ElevenLabs online" if ELEVEN_OK else "ElevenLabs offline (fallback ativo)"
        eleven_color = DS.GREEN if ELEVEN_OK else DS.YELLOW
        eleven_st = QLabel(eleven_status_txt)
        eleven_st.setStyleSheet(f"color:{eleven_color}; font-size:9px; background:transparent;")
        eleven_l.addWidget(eleven_st); eleven_l.addStretch()
        layout.addWidget(eleven_w)

        # ── Câmera + gestos ───────────────────────────────────────────────────
        cam_w = QWidget(); cam_w.setStyleSheet("background:transparent;")
        cv_layout = QVBoxLayout(cam_w)
        cv_layout.setContentsMargins(12, 6, 12, 8)
        cv_layout.setSpacing(6)

        ch = QHBoxLayout()
        cl = QLabel("CÂMERA  /  GESTOS v8")
        cl.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:2px; background:transparent;")
        ch.addWidget(cl); ch.addStretch()
        self._cam_st = QLabel("● offline")
        self._cam_st.setStyleSheet(f"color:{DS.RED}; font-size:10px; font-weight:600; background:transparent;")
        ch.addWidget(self._cam_st)
        cv_layout.addLayout(ch)

        self._cam_lbl = QLabel("Câmera inativa")
        self._cam_lbl.setAlignment(Qt.AlignCenter)
        self._cam_lbl.setFixedHeight(155)
        self._cam_lbl.setStyleSheet(
            f"background:{DS.BG0}; color:{DS.T3}; font-size:11px; "
            f"border:1px solid {DS.BORDER_BLUE}; border-radius:8px;"
        )
        cv_layout.addWidget(self._cam_lbl)

        self._fps_lbl = QLabel("FPS: —")
        self._fps_lbl.setStyleSheet(f"color:{DS.T3}; font-size:9px; background:transparent;")
        cv_layout.addWidget(self._fps_lbl)

        gc_row = QHBoxLayout(); gc_row.setSpacing(4)
        self._chip_r = QLabel("DIR: —")
        self._chip_l = QLabel("ESQ: —")
        for chip in (self._chip_r, self._chip_l):
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedHeight(24)
            chip.setStyleSheet(
                f"color:{DS.CYAN}; font-family:{DS.FONT_MONO}; font-size:9px; font-weight:700; "
                f"background:{DS.BLUE_DIM}; border:1px solid {DS.BORDER_BLUE}; border-radius:5px; letter-spacing:1px;"
            )
            gc_row.addWidget(chip)
        cv_layout.addLayout(gc_row)

        ref = QLabel(
            "✊ Punho → reset/cancelar\n"
            "☝ Indicador dir. → mover/dwell-click\n"
            "✌ 2 dedos dir. → arrastar\n"
            "🖖 4 dedos dir. → scroll\n"
            "✋ Palma dir. → ON/OFF cursor\n"
            "✋ Palma esq. → ativar escuta\n"
            "🤟 3 dedos esq. → modo volume\n"
            "L  L+Shape dir. → modo assist\n"
            "L  L+Shape esq. → ALT (tab troca janela)"
        )
        ref.setStyleSheet(f"color:{DS.T3}; font-size:9px; background:transparent; padding:2px 0;")
        cv_layout.addWidget(ref)

        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        self._cam_btn = QPushButton("▶  Câmera")
        self._cam_btn.setFixedHeight(26)
        self._cam_btn.setStyleSheet(self._btn_style(DS.BLUE))
        self._cam_btn.setCursor(Qt.PointingHandCursor)
        self._cam_btn.clicked.connect(self._toggle_cam)
        btn_row.addWidget(self._cam_btn)

        self._overlay_btn = QPushButton("◈  Overlay")
        self._overlay_btn.setFixedHeight(26)
        self._overlay_btn.setCheckable(True)
        self._overlay_btn.setStyleSheet(self._btn_style(DS.CYAN))
        self._overlay_btn.setCursor(Qt.PointingHandCursor)
        self._overlay_btn.clicked.connect(self._toggle_overlay)
        btn_row.addWidget(self._overlay_btn)
        cv_layout.addLayout(btn_row)

        layout.addWidget(cam_w)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{DS.BORDER_BLUE}; border:none;"); sep.setFixedHeight(1)
        layout.addWidget(sep)

        lw = QWidget(); lw.setStyleSheet("background:transparent;")
        lv = QVBoxLayout(lw); lv.setContentsMargins(12, 8, 12, 0); lv.setSpacing(6)
        lh = QHBoxLayout()
        lt = QLabel("LOG")
        lt.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:2px; background:transparent;")
        lh.addWidget(lt); lh.addStretch()
        cb = QPushButton("limpar")
        cb.setStyleSheet(f"background:transparent; color:{DS.T3}; border:none; font-size:9px;")
        cb.setCursor(Qt.PointingHandCursor)
        cb.clicked.connect(lambda: self._log.clear())
        lh.addWidget(cb); lv.addLayout(lh)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            f"background:transparent; color:{DS.T2}; font-family:{DS.FONT_MONO}; font-size:10px; border:none;"
        )
        lv.addWidget(self._log, 1)
        layout.addWidget(lw, 1)

        iw = QWidget()
        iw.setStyleSheet(f"background:{DS.BG0}; border-top:1px solid {DS.BORDER_BLUE};")
        iv = QVBoxLayout(iw); iv.setContentsMargins(12, 10, 12, 12); iv.setSpacing(0)
        ir = QHBoxLayout(); ir.setSpacing(6)
        pr = QLabel("›"); pr.setFixedWidth(14)
        pr.setStyleSheet(f"color:{DS.BLUE}; font-family:{DS.FONT_MONO}; font-size:14px; font-weight:700; background:transparent;")
        ir.addWidget(pr)
        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Digite um comando…")
        self._entry.setFixedHeight(30)
        self._entry.returnPressed.connect(self._send)
        ir.addWidget(self._entry, 1)
        sb = QPushButton("→"); sb.setFixedSize(30, 30)
        sb.setStyleSheet(f"""
            QPushButton {{ background:{DS.BLUE_DIM}; color:{DS.BLUE}; border:1px solid {DS.BORDER_BLUE}; border-radius:6px; font-size:13px; font-weight:700; }}
            QPushButton:hover {{ background:{DS.BLUE_MID}33; border-color:{DS.BLUE}; }}
        """)
        sb.setCursor(Qt.PointingHandCursor); sb.clicked.connect(self._send)
        ir.addWidget(sb); iv.addLayout(ir)
        layout.addWidget(iw)

        return panel

    def _btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{ background:{DS.BLUE_DIM}; color:{color}; border:1px solid {DS.BORDER_BLUE}; border-radius:5px; font-size:10px; font-weight:600; }}
            QPushButton:hover {{ background:{DS.BLUE_MID}22; border-color:{color}; }}
            QPushButton:checked {{ background:{color}33; border-color:{color}; }}
        """

    def _build_stage(self):
        stage = QWidget(); stage.setStyleSheet(f"background:{DS.BG0};")
        layout = QVBoxLayout(stage)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_top_bar())

        center = QWidget(); center.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.setAlignment(Qt.AlignCenter)
        cl.addStretch()

        nr = QHBoxLayout(); nr.setAlignment(Qt.AlignCenter)
        self._net = NetworkWidget()
        nr.addWidget(self._net)
        cl.addLayout(nr)
        cl.addSpacing(20)

        self._status_lbl = QLabel("AGUARDANDO COMANDO")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(
            f"color:{DS.BLUE_BRIGHT}; font-family:{DS.FONT_DISPLAY}; font-size:12px; "
            f"font-weight:700; letter-spacing:5px; background:transparent;"
        )
        cl.addWidget(self._status_lbl)
        cl.addSpacing(6)

        self._sub_lbl = QLabel("Diga 'JARVIS' para ativar  |  gestos: câmera no painel")
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setStyleSheet(
            f"color:{DS.T3}; font-family:{DS.FONT_MONO}; font-size:11px; letter-spacing:1px; background:transparent;"
        )
        cl.addWidget(self._sub_lbl)
        cl.addStretch()

        layout.addWidget(center, 1)
        layout.addWidget(self._build_bottom_bar())
        return stage

    def _build_top_bar(self):
        bar = QWidget(); bar.setFixedHeight(46)
        bar.setStyleSheet(f"background:{DS.BG1}; border-bottom:1px solid {DS.BORDER_BLUE};")
        layout = QHBoxLayout(bar); layout.setContentsMargins(20, 0, 20, 0); layout.setSpacing(16)

        self._clock_lbl = QLabel("00:00:00")
        self._clock_lbl.setStyleSheet(
            f"color:{DS.BLUE_BRIGHT}; font-family:{DS.FONT_DISPLAY}; font-size:15px; "
            f"font-weight:700; letter-spacing:2px; background:transparent;"
        )
        layout.addWidget(self._clock_lbl)

        self._date_lbl = QLabel("")
        self._date_lbl.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent; letter-spacing:1px;")
        layout.addWidget(self._date_lbl)
        layout.addStretch()

        vr = QHBoxLayout(); vr.setSpacing(6)
        vl = QLabel("VOL")
        vl.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:1px; background:transparent;")
        vr.addWidget(vl)
        self._vol_bar = QProgressBar()
        self._vol_bar.setRange(0, 100); self._vol_bar.setValue(50)
        self._vol_bar.setFixedSize(60, 3); self._vol_bar.setTextVisible(False)
        self._vol_bar.setStyleSheet(
            f"QProgressBar{{background:{DS.BG0};border:none;border-radius:2px;}}"
            f"QProgressBar::chunk{{background:{DS.BLUE};border-radius:2px;}}"
        )
        vr.addWidget(self._vol_bar)
        layout.addLayout(vr)

        mic = QPushButton("🎙"); mic.setFixedSize(32, 32)
        mic.setToolTip("Microfone ativo")
        mic.setStyleSheet(f"""
            QPushButton {{ background:{DS.BLUE_DIM}; color:{DS.BLUE}; border:1px solid {DS.BORDER_BLUE}; border-radius:16px; font-size:13px; }}
            QPushButton:hover {{ background:{DS.BLUE_MID}44; border-color:{DS.BLUE}; }}
        """)
        mic.setCursor(Qt.PointingHandCursor)
        mic.clicked.connect(lambda: speak("Sim, senhor.", self))
        layout.addWidget(mic)
        return bar

    def _build_bottom_bar(self):
        bar = QWidget(); bar.setFixedHeight(40)
        bar.setStyleSheet(f"background:{DS.BG1}; border-top:1px solid {DS.BORDER_BLUE};")
        layout = QHBoxLayout(bar); layout.setContentsMargins(20, 0, 20, 0); layout.setSpacing(0)

        self._sb_dot = QLabel("●")
        self._sb_dot.setStyleSheet(f"color:{DS.GREEN}; font-size:8px; background:transparent;")
        layout.addWidget(self._sb_dot)
        self._sb_lbl = QLabel("  Sistema online")
        self._sb_lbl.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent;")
        layout.addWidget(self._sb_lbl)
        layout.addStretch()

        self._stat_labels = {}
        for i, (k, key) in enumerate([("CPU","cpu"), ("RAM","ram"), ("DISCO","disk"), ("BAT","bat")]):
            if i > 0:
                sep = QLabel("|")
                sep.setStyleSheet(f"color:{DS.BORDER_BLUE}; background:transparent; padding:0 8px;")
                layout.addWidget(sep)
            rw = QHBoxLayout(); rw.setSpacing(4)
            kl = QLabel(k)
            kl.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:1px; background:transparent;")
            rw.addWidget(kl)
            vl = QLabel("—")
            vl.setStyleSheet(f"color:{DS.BLUE}; font-family:{DS.FONT_MONO}; font-size:10px; font-weight:700; background:transparent;")
            rw.addWidget(vl)
            self._stat_labels[key] = vl
            layout.addLayout(rw)
        return bar

    # ── Slots ─────────────────────────────────────────────────────────────────
    @Slot(str)
    def _on_state(self, state: str):
        self._net.set_state(state)
        cfg = {
            "idle":       ("AGUARDANDO COMANDO",  "Diga 'JARVIS' para ativar  |  gestos: câmera no painel", DS.BLUE_BRIGHT),
            "listening":  ("OUVINDO",             "Escutando você…",           DS.CYAN),
            "processing": ("PROCESSANDO",         "Analisando comando…",       DS.BLUE),
            "speaking":   ("RESPONDENDO",         "JARVIS falando…",           DS.BLUE_BRIGHT),
        }.get(state, ("AGUARDANDO COMANDO", "Diga 'JARVIS' para ativar", DS.BLUE_BRIGHT))
        main_txt, sub_txt, color = cfg
        self._status_lbl.setText(main_txt)
        self._status_lbl.setStyleSheet(
            f"color:{color}; font-family:{DS.FONT_DISPLAY}; font-size:12px; "
            f"font-weight:700; letter-spacing:5px; background:transparent;"
        )
        self._sub_lbl.setText(sub_txt)

    @Slot(str, str)
    def _on_gesture_adv(self, r_g: str, l_g: str):
        rl = GestureEngine.GESTURE_LABELS.get(r_g, r_g)
        ll = GestureEngine.GESTURE_LABELS.get(l_g, l_g)
        self._chip_r.setText(f"D {rl}")
        self._chip_l.setText(f"E {ll}")

    def _toggle_cam(self):
        if not CV2_OK:
            self.add_log("mediapipe/opencv não instalado", "erro")
            return
        if not self._cam_on:
            self._start_cam()
        else:
            self._stop_cam()

    def _start_cam(self):
        if not self._engine.start():
            self.add_log("Webcam não encontrada", "erro")
            return
        self._cam_on = True
        self._cam_btn.setText("■  Parar")
        self._cam_btn.setStyleSheet(f"""
            QPushButton {{ background:{DS.RED}22; color:{DS.RED}; border:1px solid {DS.RED}66; border-radius:5px; font-size:10px; font-weight:600; }}
            QPushButton:hover {{ background:{DS.RED}44; }}
        """)
        self._cam_st.setText("● ao vivo")
        self._cam_st.setStyleSheet(f"color:{DS.GREEN}; font-size:10px; font-weight:600; background:transparent;")
        self._sb_lbl.setText("  Câmera ativa — gestos v8 habilitados")
        self._sb_lbl.setStyleSheet(f"color:{DS.GREEN}; font-size:10px; background:transparent;")
        self.add_log("GestureEngine v8 iniciado", "gesto")
        speak("Câmera ativada. Controle por gestos está online, senhor.", self)

        if self._ctrl:
            self._ctrl._dpr = QApplication.primaryScreen().devicePixelRatio()

        threading.Thread(target=self._cam_loop, daemon=True).start()

    def _stop_cam(self):
        self._cam_on = False
        self._engine.stop()
        self._cam_btn.setText("▶  Câmera")
        self._cam_btn.setStyleSheet(self._btn_style(DS.BLUE))
        self._cam_st.setText("● offline")
        self._cam_st.setStyleSheet(f"color:{DS.RED}; font-size:10px; font-weight:600; background:transparent;")
        self._cam_lbl.clear()
        self._cam_lbl.setText("Câmera inativa")
        self._chip_r.setText("DIR: —")
        self._chip_l.setText("ESQ: —")
        self._sb_lbl.setText("  Sistema online")
        self._sb_lbl.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent;")
        self._fps_lbl.setText("FPS: —")
        self.add_log("Câmera desativada", "info")
        speak("Câmera desativada, senhor.", self)
        self._overlay.set_overlay_visible(False)
        self._overlay_btn.setChecked(False)

    def _cam_loop(self):
        while self._cam_on:
            frame, hands = self._engine.read()

            if self._ctrl and hands is not None:
                self._ctrl.process(hands if hands else [])

            self._fps_count += 1
            now = time.time()
            elapsed = now - self._fps_time
            if elapsed >= 1.0:
                fps = self._fps_count / elapsed
                self._fps_count = 0
                self._fps_time  = now
                self._fps_lbl.setText(f"FPS: {fps:.0f}")
                if fps < 10 and self._ctrl:
                    self._ctrl.clear_inputs()
                    self.add_log("⚠ FPS baixo — inputs resetados", "alerta")

            if frame is not None:
                try:
                    sm = cv2.resize(frame, (251, 155))
                    self.sig_cam_img.emit(sm)
                except Exception:
                    pass

            time.sleep(0.010)

    @Slot(object)
    def _update_cam_pixmap(self, frame_bgr):
        try:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self._cam_lbl.setPixmap(
                QPixmap.fromImage(img).scaled(
                    self._cam_lbl.width(), self._cam_lbl.height(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            self._cam_lbl.setText("")
        except Exception:
            pass

    def _toggle_overlay(self):
        visible = self._overlay_btn.isChecked()
        self._overlay.set_overlay_visible(visible)
        estado = "ativo" if visible else "inativo"
        self.add_log(f"◈ Overlay {estado}", "info")

    def update_stats(self, info): self.sig_stats.emit(info)

    @Slot(dict)
    def _apply_stats(self, info):
        for k, lbl in self._stat_labels.items():
            if k in info:
                lbl.setText(info[k])

    def set_volume(self, pct): self.sig_volume.emit(pct)

    def add_log(self, text: str, tag: str = ""):
        self.sig_log.emit(text, tag)

    @Slot(str, str)
    def _append_log(self, text: str, tag: str):
        if tag == "fps_internal" or not text:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        colors = {
            "jarvis": DS.BLUE_BRIGHT, "user": DS.GREEN, "gesto": DS.CYAN,
            "alerta": DS.YELLOW, "erro": DS.RED, "info": DS.T3,
        }
        color = colors.get(tag, DS.T2)
        self._log.setTextColor(QColor(DS.T3))
        self._log.append(f"[{ts}] ")
        c = self._log.textCursor(); c.movePosition(QTextCursor.End); self._log.setTextCursor(c)
        self._log.setTextColor(QColor(color))
        self._log.insertPlainText(text)
        self._log.moveCursor(QTextCursor.End)
        if tag == "jarvis":
            self.sig_state.emit("speaking")
        elif tag == "user":
            self.sig_state.emit("processing")

    def _send(self):
        q = self._entry.text().strip()
        if not q: return
        self._entry.clear()
        self.add_log(f"YOU › {q}", "user")
        speak(jarvis_response(q), self)
        threading.Thread(target=cmd, args=(q, self), daemon=True).start()

    def _clock_tick(self):
        n = datetime.datetime.now()
        self._clock_lbl.setText(n.strftime("%H:%M:%S"))
        self._date_lbl.setText(n.strftime("%d/%m · %a").upper())

    def _stats_tick(self):
        self.update_stats(sys_info())

    def menu_up(self):
        self.menu_idx = (self.menu_idx - 1) % len(MENU_ITEMS)
        self.add_log(f"Menu ↑ → {MENU_ITEMS[self.menu_idx][0]}", "gesto")

    def menu_down(self):
        self.menu_idx = (self.menu_idx + 1) % len(MENU_ITEMS)
        self.add_log(f"Menu ↓ → {MENU_ITEMS[self.menu_idx][0]}", "gesto")

    def menu_confirm(self):
        lbl_t, mc = MENU_ITEMS[self.menu_idx]
        self.add_log(f"Gesto confirm → {lbl_t}", "gesto")
        self._run(mc)

    def _run(self, action):
        if callable(action):
            threading.Thread(target=action, daemon=True).start()
        else:
            self.add_log(f"CMD › {action}", "user")
            speak(jarvis_response(action), self)
            threading.Thread(target=cmd, args=(action, self), daemon=True).start()

    def closeEvent(self, event):
        self._cam_on = False
        self._engine.stop()
        self._scanner.stop()
        self._overlay.close()
        event.accept()

    def run(self):
        self.add_log("Inicializando JARVIS v8.1 — ElevenLabs…", "info")
        eleven_msg = "ElevenLabs online" if ELEVEN_OK else "ElevenLabs offline — usando fallback de voz"
        self.add_log(eleven_msg, "info" if ELEVEN_OK else "alerta")

        def _boot():
            _speak_ready.wait(timeout=20)
            speak("JARVIS online. Todos os módulos carregados. Pronto para seus comandos, senhor.", self)

        threading.Thread(target=_boot, daemon=True).start()
        self.show()


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(DS.BG0))
    pal.setColor(QPalette.WindowText,      QColor(DS.T1))
    pal.setColor(QPalette.Base,            QColor(DS.BG1))
    pal.setColor(QPalette.AlternateBase,   QColor(DS.BG2))
    pal.setColor(QPalette.Text,            QColor(DS.T1))
    pal.setColor(QPalette.Button,          QColor(DS.BG1))
    pal.setColor(QPalette.ButtonText,      QColor(DS.T1))
    pal.setColor(QPalette.Highlight,       QColor(DS.BLUE_DIM))
    pal.setColor(QPalette.HighlightedText, QColor(DS.BLUE_BRIGHT))
    pal.setColor(QPalette.Link,            QColor(DS.BLUE))
    pal.setColor(QPalette.ToolTipBase,     QColor(DS.BG2))
    pal.setColor(QPalette.ToolTipText,     QColor(DS.T1))
    app.setPalette(pal)

    ui = JarvisUI()
    ui.run()
    sys.exit(app.exec())
