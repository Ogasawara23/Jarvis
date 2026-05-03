"""
╔══════════════════════════════════════════════════════════════════════╗
║        J.A.R.V.I.S  —  PARTICLE NETWORK  v7.0  (PySide6)           ║
║  Interface de voz • Rede de partículas azul • Gestos simples        ║
╠══════════════════════════════════════════════════════════════════════╣
║  pip install mediapipe opencv-python numpy pyautogui                 ║
║  pip install SpeechRecognition psutil pywin32 pycaw comtypes         ║
║  pip install edge-tts pygame PySide6                                 ║
╚══════════════════════════════════════════════════════════════════════╝

══════════════════════════════════════════════════════════════════════
  PARÂMETROS FÁCEIS DE AJUSTAR
══════════════════════════════════════════════════════════════════════
  Partículas:
    PARTICLE_COUNT    = quantidade de partículas na rede
    PARTICLE_SPEED    = velocidade base de movimento
    CONNECTION_DIST   = distância máxima para conectar partículas
    PULSE_SPEED       = velocidade do pulso central

  Gestos (MediaPipe):
    GESTURE_HOLD_FRAMES   = frames consecutivos para confirmar gesto
    GESTURE_COOLDOWN_SEC  = segundos de espera entre gestos
    PINCH_THRESHOLD       = distância do pinch (menor = mais fechado)
    OPEN_PALM_FINGERS     = mínimo de dedos para "mão aberta"

  Cores (modificar no DS):
    BLUE / BLUE_BRIGHT / BLUE_DIM  — paleta de azul
══════════════════════════════════════════════════════════════════════
"""

# ── Parâmetros ajustáveis ────────────────────────────────────────────
PARTICLE_COUNT     = 55      # quantidade de partículas
PARTICLE_SPEED     = 0.30    # velocidade base de movimento
CONNECTION_DIST    = 130     # distância px para conectar (pseudo-3D projetado)
PULSE_SPEED        = 0.018   # velocidade do pulso do núcleo

GESTURE_HOLD_FRAMES  = 10    # frames para confirmar um gesto (anti-falso-positivo)
GESTURE_COOLDOWN_SEC = 1.2   # segundos entre gestos disparados
PINCH_THRESHOLD      = 0.048 # limiar de pinch (0.03 bem fechado, 0.06 relaxado)
OPEN_PALM_FINGERS    = 4     # mínimo dedos para mão aberta
# ────────────────────────────────────────────────────────────────────

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QLineEdit, QTextEdit, QProgressBar,
    QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRect
from PySide6.QtGui import (
    QFont, QColor, QPalette, QTextCursor, QPixmap, QImage,
    QPainter, QRadialGradient, QBrush, QPen,
)

import sys, threading, datetime, os, random, time, subprocess
import platform, socket, ctypes, queue, math, asyncio
import tempfile, hashlib
from pathlib import Path

# ── Optional imports ─────────────────────────────────────────────────
try:
    import cv2, mediapipe as mp, numpy as np
    CV2_OK = True
except: CV2_OK = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0
    AG_OK = True
except: AG_OK = False

try:
    import psutil; PS_OK = True
except: PS_OK = False

try:
    import speech_recognition as sr; SR_OK = True
except: SR_OK = False

try:
    import edge_tts; EDGE_OK = True
except: EDGE_OK = False

try:
    import pygame; pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    PG_OK = True
except: PG_OK = False

try:
    import webbrowser as wb; WB_OK = True
except: WB_OK = False


# ═══════════════════════════════════════════════════════════
# DESIGN SYSTEM — Azul tecnológico
# ═══════════════════════════════════════════════════════════
class DS:
    # Fundos
    BG0 = "#030810"   # fundo abissal
    BG1 = "#060D1A"   # sidebar
    BG2 = "#0A1424"   # card

    # Azul — paleta principal
    BLUE        = "#1A8FFF"   # azul principal
    BLUE_BRIGHT = "#4DB8FF"   # azul brilhante
    BLUE_DIM    = "#0A2040"   # azul escuro bg
    BLUE_MID    = "#0D5099"   # meio
    BLUE_GLOW   = "#00AAFF"   # glow

    # Ciano complementar
    CYAN        = "#00D4FF"
    CYAN_DIM    = "#002A38"

    # Status
    GREEN  = "#00E5A0"
    RED    = "#FF3358"
    YELLOW = "#FFD166"
    AMBER  = "#FF8C00"

    # Texto
    T1 = "#D0E8FF"   # primário azulado
    T2 = "#5A7A99"   # secundário
    T3 = "#1A3050"   # terciário

    BORDER      = "#0D1E30"
    BORDER_BLUE = "#0D3060"

    FONT_DISPLAY = "Orbitron, Rajdhani, Consolas, monospace"
    FONT_MONO    = "JetBrains Mono, Consolas, monospace"
    FONT_UI      = "Segoe UI, SF Pro Display, system-ui, sans-serif"


# ── QSS Global ───────────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════
# PARTICLE — ponto pseudo-3D da rede
# ═══════════════════════════════════════════════════════════
class Particle:
    """Partícula com posição 3D projetada para 2D."""
    def __init__(self, cx: float, cy: float, radius: float):
        self.reset(cx, cy, radius)

    def reset(self, cx: float, cy: float, radius: float):
        # Posição 3D em coordenadas esféricas
        theta = random.uniform(0, 2 * math.pi)
        phi   = random.uniform(0, math.pi)
        r     = random.uniform(0.3, 1.0) * radius

        self.x3 = r * math.sin(phi) * math.cos(theta)
        self.y3 = r * math.sin(phi) * math.sin(theta)
        self.z3 = r * math.cos(phi)

        # Velocidade angular lenta
        self.vt = random.uniform(-0.003, 0.003) * PARTICLE_SPEED
        self.vp = random.uniform(-0.002, 0.002) * PARTICLE_SPEED
        self.vr = 0.0

        self._r0    = r
        self._theta = theta
        self._phi   = phi
        self.alpha  = random.uniform(0.4, 1.0)
        self.size   = random.uniform(1.5, 3.5)

    def update(self, state: str):
        speed_mult = {"idle": 0.5, "listening": 1.4, "processing": 2.2, "speaking": 1.0}.get(state, 1.0)
        self._theta += self.vt * speed_mult
        self._phi   += self.vp * speed_mult
        r = self._r0

        self.x3 = r * math.sin(self._phi) * math.cos(self._theta)
        self.y3 = r * math.sin(self._phi) * math.sin(self._theta)
        self.z3 = r * math.cos(self._phi)

    def project(self, cx: float, cy: float, fov: float = 400) -> tuple:
        """Retorna (px, py, scale) com projeção perspectiva."""
        z = self.z3 + fov
        if z < 1: z = 1
        scale = fov / z
        px = cx + self.x3 * scale
        py = cy + self.y3 * scale
        depth = (self.z3 + self._r0) / (2 * self._r0)  # 0..1
        return px, py, scale, depth


# ═══════════════════════════════════════════════════════════
# NETWORK WIDGET — visualização central de rede de dados
# ═══════════════════════════════════════════════════════════
class NetworkWidget(QWidget):
    """Rede de partículas 3D com conexões — núcleo visual da Jarvis."""

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
        self._angle  = 0.0
        self._energy = 0.0

        self._particles: list[Particle] = []
        self._init_particles()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(20)  # 50fps — bom custo-benefício

    def _init_particles(self):
        cx = self.width()  / 2
        cy = self.height() / 2
        R  = min(cx, cy) * 0.82
        self._particles = [Particle(cx, cy, R) for _ in range(PARTICLE_COUNT)]

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _tick(self):
        self._pulse = (self._pulse + PULSE_SPEED) % (2 * math.pi)
        self._wave  = (self._wave  + 0.035)       % (2 * math.pi)
        self._angle = (self._angle + 0.3)         % 360

        for p in self._particles:
            p.update(self._state)

        self.update()

    # ── Estado → cor ──────────────────────────────────────────────────
    def _state_colors(self):
        s = self._state
        if s == self.LISTENING:
            return (
                QColor(30, 150, 255),    # partícula
                QColor(20, 120, 220, 90),# conexão
                QColor(0,  160, 255, 30),# glow outer
                QColor(60, 180, 255),    # ring
            )
        elif s == self.PROCESSING:
            return (
                QColor(0,  220, 255),
                QColor(0,  180, 220, 90),
                QColor(0,  200, 255, 35),
                QColor(0,  230, 255),
            )
        elif s == self.SPEAKING:
            return (
                QColor(80, 190, 255),
                QColor(40, 150, 240, 100),
                QColor(50, 170, 255, 40),
                QColor(100,210,255),
            )
        else:  # idle
            return (
                QColor(20,  80, 160),
                QColor(15,  60, 130, 60),
                QColor(10,  50, 120, 15),
                QColor(30, 100, 180),
            )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h   = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        R      = min(cx, cy) * 0.82
        pulse  = math.sin(self._pulse)
        wave   = self._wave

        c_part, c_conn, c_glow, c_ring = self._state_colors()

        # ── Fundo: glow radial central ────────────────────────────────
        bg_grad = QRadialGradient(cx, cy, R * 0.9)
        glow_in = QColor(c_glow); glow_in.setAlpha(int(25 + 15 * abs(pulse)))
        bg_grad.setColorAt(0.0, glow_in)
        bg_grad.setColorAt(0.5, QColor(c_glow.red(), c_glow.green(), c_glow.blue(), 8))
        bg_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), R * 1.05, R * 1.05)

        # ── Projetar partículas ───────────────────────────────────────
        projected = []
        for p in self._particles:
            px, py, scale, depth = p.project(cx, cy)
            projected.append((px, py, scale, depth, p))

        # Ordenar por profundidade (z) — as mais atrás primeiro
        projected.sort(key=lambda x: x[2])

        # ── Conexões ──────────────────────────────────────────────────
        n = len(projected)
        for i in range(n):
            ax, ay, sa, da, pa = projected[i]
            for j in range(i + 1, n):
                bx, by, sb, db, pb = projected[j]
                dist = math.hypot(ax - bx, ay - by)
                if dist < CONNECTION_DIST:
                    strength = 1.0 - dist / CONNECTION_DIST
                    alpha    = int(180 * strength * (da + db) / 2)
                    if self._state == self.IDLE:
                        alpha = int(alpha * 0.45)
                    lc = QColor(c_conn)
                    lc.setAlpha(max(0, min(255, alpha)))
                    pen = QPen(lc, max(0.4, strength * 1.4))
                    painter.setPen(pen)
                    painter.drawLine(QPointF(ax, ay), QPointF(bx, by))

        # ── Partículas ────────────────────────────────────────────────
        painter.setPen(Qt.NoPen)
        for px, py, scale, depth, p in projected:
            base_alpha = int(220 * depth * p.alpha)
            if self._state == self.IDLE:
                base_alpha = int(base_alpha * 0.55)

            sz = p.size * max(0.6, scale * 0.012)
            sz = max(1.2, min(sz, 5.0))

            # Glow ao redor da partícula
            g = QRadialGradient(px, py, sz * 3)
            gc = QColor(c_part); gc.setAlpha(int(base_alpha * 0.35))
            g.setColorAt(0.0, gc)
            g.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(px, py), sz * 3, sz * 3)

            # Ponto sólido
            pc = QColor(c_part); pc.setAlpha(base_alpha)
            painter.setBrush(QBrush(pc))
            painter.drawEllipse(QPointF(px, py), sz, sz)

        # ── Anéis expansivos ──────────────────────────────────────────
        n_rings = 3
        for i in range(n_rings):
            progress = ((self._pulse / (2 * math.pi)) + i / n_rings) % 1.0
            ring_r   = R * 0.25 + progress * R * 0.65
            alpha    = int(100 * (1.0 - progress) * (0.5 + 0.5 * abs(pulse)))
            if self._state == self.IDLE:
                alpha = int(alpha * 0.3)
            rc = QColor(c_ring); rc.setAlpha(alpha)
            pen = QPen(rc, 0.8)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # ── Arco giratório (HUD scanner) ──────────────────────────────
        arc_r   = R * 0.88
        arc_pen = QPen(QColor(c_ring))
        arc_pen.setWidth(1)
        arc_pen.setCapStyle(Qt.RoundCap)
        arc_r2  = QColor(c_ring); arc_r2.setAlpha(50)
        arc_pen.setColor(arc_r2)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.NoBrush)
        arc_rect = QRect(int(cx - arc_r), int(cy - arc_r), int(arc_r * 2), int(arc_r * 2))
        # Círculo estrutural tênue
        painter.drawEllipse(QPointF(cx, cy), arc_r, arc_r)

        # Arco brilhante
        span = 60 if self._state == self.IDLE else 100
        bright_pen = QPen(QColor(c_ring)); bright_pen.setWidth(2); bright_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bright_pen)
        painter.drawArc(arc_rect, int(-self._angle * 16), span * 16)

        # ── Núcleo central ────────────────────────────────────────────
        core_r = R * 0.12 + R * 0.025 * abs(pulse)
        core_g = QRadialGradient(cx, cy, core_r)
        bright = QColor(c_ring); bright.setAlpha(255)
        mid    = QColor(c_part); mid.setAlpha(160)
        edge   = QColor(c_part); edge.setAlpha(20)
        core_g.setColorAt(0.0, bright)
        core_g.setColorAt(0.5, mid)
        core_g.setColorAt(1.0, edge)
        painter.setBrush(QBrush(core_g))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # Barra de voz radial (estado speaking/listening)
        if self._state in (self.SPEAKING, self.LISTENING, self.PROCESSING):
            n_bars   = 48
            bar_base = R * 0.52
            bar_max  = R * 0.18
            for i in range(n_bars):
                ang   = math.radians(i * (360 / n_bars))
                phase = i * (2 * math.pi / n_bars)
                if self._state == self.SPEAKING:
                    hb = bar_max * (0.2 + 0.8 * abs(math.sin(wave * 3 + phase)))
                elif self._state == self.PROCESSING:
                    hb = bar_max * (0.3 + 0.7 * abs(math.sin(wave * 5 + phase * 2)))
                else:
                    hb = bar_max * (0.1 + 0.4 * abs(math.sin(wave * 2 + phase)))

                x1 = cx + bar_base * math.cos(ang)
                y1 = cy + bar_base * math.sin(ang)
                x2 = cx + (bar_base + hb) * math.cos(ang)
                y2 = cy + (bar_base + hb) * math.sin(ang)

                ba = int(160 * (hb / bar_max))
                bc = QColor(c_ring); bc.setAlpha(max(20, ba))
                bpen = QPen(bc, 1.5, Qt.SolidLine, Qt.RoundCap)
                painter.setPen(bpen)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        painter.end()


# ═══════════════════════════════════════════════════════════
# SIMPLE GESTURE DETECTOR — gestos simplificados com debounce
# ═══════════════════════════════════════════════════════════
class SimpleGestureDetector:
    """
    Detecta apenas 3 gestos simples, confiáveis e com cooldown:
      OPEN_PALM  — mão aberta (≥4 dedos erguidos)  → ativar Jarvis
      FIST       — punho fechado                    → cancelar/parar
      PINCH      — polegar+indicador próximos       → confirmar/click

    A mão esquerda muda o modo do cursor (mantida do sistema anterior).
    """

    OPEN_PALM = "OPEN_PALM"
    FIST      = "FIST"
    PINCH     = "PINCH"
    NONE      = "NONE"

    TIPS = [4, 8, 12, 16, 20]

    def __init__(self):
        self.ok = CV2_OK
        if not self.ok: return

        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,          # apenas 1 mão — mais leve e confiável
            min_detection_confidence=0.80,
            min_tracking_confidence=0.75,
        )
        self.draw   = mp.solutions.drawing_utils
        self.cap    = None

        # Estado de debounce
        self._hold_count     = 0
        self._hold_gesture   = self.NONE
        self._last_confirmed = 0.0  # timestamp do último gesto disparado
        self._last_raw       = self.NONE

    # ── Câmera ───────────────────────────────────────────────────────
    def start(self) -> bool:
        if not self.ok: return False
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def stop(self):
        if self.cap: self.cap.release()
        self.cap = None

    # ── Detecção de dedos ─────────────────────────────────────────────
    def _count_fingers(self, lm) -> int:
        count = 0
        # Polegar (eixo x)
        if lm[4].x < lm[3].x: count += 1
        # Demais dedos (eixo y)
        for tip in self.TIPS[1:]:
            if lm[tip].y < lm[tip - 2].y: count += 1
        return count

    def _is_fist(self, lm) -> bool:
        return sum(1 for t in self.TIPS[1:] if lm[t].y > lm[t - 2].y) >= 4

    def _pinch_dist(self, lm) -> float:
        return math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y)

    def _classify(self, lm) -> str:
        if self._is_fist(lm):
            return self.FIST
        if self._pinch_dist(lm) < PINCH_THRESHOLD:
            return self.PINCH
        if self._count_fingers(lm) >= OPEN_PALM_FINGERS:
            return self.OPEN_PALM
        return self.NONE

    # ── Leitura ──────────────────────────────────────────────────────
    def read(self):
        """
        Retorna (frame_bgr, confirmed_gesture, raw_gesture).
          confirmed_gesture — gesto disparado após debounce (ou NONE)
          raw_gesture       — gesto detectado no frame atual
        """
        if not self.ok or not self.cap:
            return None, self.NONE, self.NONE

        ret, frame = self.cap.read()
        if not ret:
            return None, self.NONE, self.NONE

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res   = self.hands.process(rgb)

        raw       = self.NONE
        confirmed = self.NONE

        if res.multi_hand_landmarks:
            hlm = res.multi_hand_landmarks[0]
            lm  = hlm.landmark
            raw = self._classify(lm)

            # Desenho discreto sobre o frame
            self.draw.draw_landmarks(
                frame, hlm, mp.solutions.hands.HAND_CONNECTIONS,
                self.draw.DrawingSpec(color=(30, 150, 255), thickness=1, circle_radius=3),
                self.draw.DrawingSpec(color=(10,  80, 160), thickness=1),
            )
            # Label do gesto
            label = {"OPEN_PALM": "OPEN", "FIST": "FIST", "PINCH": "PINCH"}.get(raw, "")
            if label:
                cv2.putText(frame, label,
                    (int(lm[0].x * frame.shape[1]) - 20, int(lm[0].y * frame.shape[0]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 180, 255), 1)

            # ── Debounce / hold ───────────────────────────────────────
            if raw == self._hold_gesture and raw != self.NONE:
                self._hold_count += 1
            else:
                self._hold_gesture = raw
                self._hold_count   = 1

            now = time.time()
            if (self._hold_count >= GESTURE_HOLD_FRAMES and
                    now - self._last_confirmed >= GESTURE_COOLDOWN_SEC and
                    raw != self.NONE):
                confirmed            = raw
                self._last_confirmed = now
                self._hold_count     = 0  # reset para não disparar duas vezes

        else:
            self._hold_count   = 0
            self._hold_gesture = self.NONE

        self._last_raw = raw
        return frame, confirmed, raw


# ═══════════════════════════════════════════════════════════
# VOICE ENGINE — inalterada
# ═══════════════════════════════════════════════════════════
CACHE_DIR    = Path(tempfile.gettempdir()) / "jarvis_voice_cache"
CACHE_DIR.mkdir(exist_ok=True)
JARVIS_VOICE = "en-GB-RyanNeural"
JARVIS_RATE  = "-5%"
JARVIS_PITCH = "-8Hz"

PRECACHE_PHRASES = [
    "Yes, sir.", "Of course, sir.", "Certainly, sir.", "Right away, sir.",
    "All systems are operational, sir.", "As you wish, sir.", "I understand, sir.",
    "Camera activated. Gesture control is now online, sir.", "Camera deactivated, sir.",
    "Opening Google, sir.", "Opening YouTube, sir.", "Opening Spotify, sir.",
    "Opening Discord, sir.", "Opening GitHub, sir.", "Opening WhatsApp, sir.",
    "Opening Netflix, sir.", "Volume increased, sir.", "Volume decreased, sir.",
    "Audio muted, sir.", "Screenshot captured and saved, sir.",
    "Locking the workstation, sir.", "Shutting down in five seconds, sir.",
    "Restarting the system, sir.", "Command cancelled, sir.",
    "Gesture confirmed, sir.", "Listening, sir.",
    "JARVIS online. All modules loaded. Ready for your command, sir.",
]

_voz_q       = queue.Queue()
_speak_ready = threading.Event()

def _cache_key(t): return hashlib.md5(t.encode()).hexdigest()
def _cache_path(t): return CACHE_DIR / f"{_cache_key(t)}.mp3"

async def _generate_audio(text, path):
    c = edge_tts.Communicate(text, JARVIS_VOICE, rate=JARVIS_RATE, pitch=JARVIS_PITCH)
    await c.save(str(path))

def _ensure_cached(text):
    path = _cache_path(text)
    if not path.exists():
        try: asyncio.run(_generate_audio(text, path))
        except: return None
    return path

def _precache_worker():
    for p in PRECACHE_PHRASES: _ensure_cached(p)
    _speak_ready.set()

def _play_audio(path):
    if not PG_OK or not path or not path.exists(): return
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): time.sleep(0.05)
    except: pass

def _voz_worker():
    while True:
        text = _voz_q.get()
        try:
            if EDGE_OK and PG_OK:
                path = _ensure_cached(text)
                if path: _play_audio(path)
                else: _pyttsx3_fallback(text)
            else: _pyttsx3_fallback(text)
        except: pass
        _voz_q.task_done()

def _pyttsx3_fallback(text):
    try:
        import pyttsx3
        e = pyttsx3.init(); e.setProperty('rate', 160)
        for v in e.getProperty('voices'):
            if 'english' in v.name.lower(): e.setProperty('voice', v.id); break
        e.say(text); e.runAndWait()
    except: pass

threading.Thread(target=_voz_worker,     daemon=True).start()
threading.Thread(target=_precache_worker, daemon=True).start()

def speak(text, ui=None):
    if ui: ui.add_log(f"JARVIS › {text}", "jarvis")
    _voz_q.put(text)

PTBR_TO_EN = {
    "jarvis": "Yes, sir.", "sim": "Of course, sir.", "ok": "Right away, sir.",
    "obrigado": "My pleasure, sir.", "google": "Opening Google, sir.",
    "youtube": "Opening YouTube, sir.", "spotify": "Opening Spotify, sir.",
    "discord": "Opening Discord, sir.", "whatsapp": "Opening WhatsApp, sir.",
    "netflix": "Opening Netflix, sir.", "github": "Opening GitHub, sir.",
    "chatgpt": "Opening ChatGPT, sir.", "gmail": "Opening Gmail, sir.",
    "status": "Fetching system diagnostics, sir.",
    "screenshot": "Screenshot captured and saved to your Pictures folder, sir.",
    "bloqueia": "Locking the workstation, sir.",
    "desliga": "Initiating shutdown sequence in five seconds, sir.",
    "reinicia": "Restarting the system, sir.",
    "sair": "Shutting down JARVIS. Good day, sir.",
}

def jarvis_response(q):
    q = q.lower().strip()
    for key, resp in PTBR_TO_EN.items():
        if key in q and resp: return resp
    return random.choice([
        "Understood, sir.", "Processing your request, sir.",
        "Command acknowledged, sir.", "Noted, sir.",
        "I'm on it, sir.", "Affirmative, sir.", "Consider it done, sir.",
    ])


# ═══════════════════════════════════════════════════════════
# SYSTEM
# ═══════════════════════════════════════════════════════════
def sys_info():
    try:
        cpu  = psutil.cpu_percent(interval=0.2) if PS_OK else 0
        ram  = psutil.virtual_memory()          if PS_OK else None
        disk = psutil.disk_usage('/')           if PS_OK else None
        bat  = psutil.sensors_battery()         if PS_OK else None
        host = socket.gethostname()
        ip   = socket.gethostbyname(host)
        return dict(
            cpu  = f"{cpu:.0f}%",
            ram  = f"{ram.percent:.0f}%" if ram  else "N/A",
            disk = f"{disk.percent:.0f}%" if disk else "N/A",
            bat  = (f"{bat.percent:.0f}%{'⚡' if bat.power_plugged else ''}") if bat else "N/A",
            ip=ip, host=host,
        )
    except: return {k: "?" for k in ["cpu","ram","disk","bat","ip","host"]}

def vol_ctrl(d):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        dev   = AudioUtilities.GetSpeakers()
        iface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol   = cast(iface, POINTER(IAudioEndpointVolume))
        if d == 'up':  vol.SetMasterVolumeLevel(min(vol.GetMasterVolumeLevel()+2., 0.), None)
        elif d == 'dn':vol.SetMasterVolumeLevel(max(vol.GetMasterVolumeLevel()-2.,-65.25), None)
        elif d == 'mu':vol.SetMute(not vol.GetMute(), None)
    except:
        if AG_OK:
            {'up': lambda: pyautogui.press('volumeup'),
             'dn': lambda: pyautogui.press('volumedown'),
             'mu': lambda: pyautogui.press('volumemute')}.get(d, lambda: None)()


# ═══════════════════════════════════════════════════════════
# COMMAND HANDLER — inalterado
# ═══════════════════════════════════════════════════════════
SITES = {
    "youtube":  ("https://youtube.com", "YouTube"),
    "google":   ("https://google.com",  "Google"),
    "github":   ("https://github.com",  "GitHub"),
    "chatgpt":  ("https://chat.openai.com","ChatGPT"),
    "gmail":    ("https://mail.google.com","Gmail"),
    "whatsapp": ("https://web.whatsapp.com","WhatsApp"),
    "netflix":  ("https://netflix.com", "Netflix"),
    "twitch":   ("https://twitch.tv",   "Twitch"),
    "reddit":   ("https://reddit.com",  "Reddit"),
    "linkedin": ("https://linkedin.com","LinkedIn"),
}

MENU_ITEMS = [
    ("Google","google"),("YouTube","youtube"),("Spotify","spotify"),
    ("WhatsApp","whatsapp"),("VS Code","vs code"),("Status","status"),
    ("Discord","discord"),("Hora","hora"),("Screenshot","screenshot"),("Sair","sair"),
]

def cmd(query, ui):
    q = query.lower().strip()
    if not q: return
    if "hora" in q or "que horas" in q:
        speak(f"The current time is {datetime.datetime.now().strftime('%H:%M')}, sir.", ui); return
    if "data" in q or "hoje" in q:
        speak(f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}, sir.", ui); return
    if "status" in q or "sistema" in q:
        i = sys_info()
        speak(f"CPU at {i['cpu']}, RAM at {i['ram']}. All systems nominal, sir.", ui)
        ui.update_stats(i); return
    if "desliga" in q:
        speak("Initiating shutdown. Five seconds, sir.", ui)
        time.sleep(5); os.system("shutdown /s /t 1"); return
    if "reinicia" in q:
        speak("Restarting, sir.", ui); os.system("shutdown /r /t 3"); return
    if "bloqueia" in q or "trava" in q:
        speak("Locking the workstation, sir.", ui)
        try: ctypes.windll.user32.LockWorkStation()
        except: pass; return
    if "volume" in q:
        if any(x in q for x in ["aumenta","sobe","mais","cima"]):
            vol_ctrl('up'); speak("Volume increased, sir.", ui)
        elif any(x in q for x in ["diminui","baixa","menos"]):
            vol_ctrl('dn'); speak("Volume decreased, sir.", ui)
        elif any(x in q for x in ["muta","silencia","mudo"]):
            vol_ctrl('mu'); speak("Audio muted, sir.", ui)
        return
    for k, (url, name) in SITES.items():
        if k in q:
            frase = q.replace(k,"").replace("abre","").replace("pesquisa","").strip()
            full  = url
            if frase and k == "youtube": full = f"https://www.youtube.com/results?search_query={frase.replace(' ','+')}"
            elif frase and k == "google": full = f"https://www.google.com/search?q={frase.replace(' ','+')}"
            if WB_OK: wb.open(full)
            speak(f"Opening {name}, sir.", ui); return
    if "spotify" in q:
        try: os.startfile("spotify:")
        except:
            if WB_OK: wb.open("https://open.spotify.com")
        speak("Opening Spotify, sir.", ui); return
    local_apps = {
        "discord":    os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
        "notepad":    "notepad.exe", "bloco de notas": "notepad.exe",
        "calculadora":"calc.exe",    "paint": "mspaint.exe",
        "explorer":   "explorer.exe","gerenciador": "taskmgr.exe",
        "vs code":    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        "vscode":     os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    }
    for k, exe in local_apps.items():
        if k in q:
            try: subprocess.Popen([exe])
            except: pass
            speak(f"Launching {k}, sir.", ui); return
    if "screenshot" in q or "print" in q or "captura" in q:
        if AG_OK:
            try:
                p = os.path.join(Path.home(),"Pictures",
                    f"jarvis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                pyautogui.screenshot(p)
                speak("Screenshot captured, sir.", ui)
                ui.add_log(f"📸 {p}", "info")
            except: speak("Unable to capture screenshot, sir.", ui)
        return
    if "timer" in q or "alarme" in q:
        nums = [int(s) for s in q.split() if s.isdigit()]
        if nums:
            secs = nums[0]*60 if "minuto" in q else nums[0]
            speak(f"Timer set for {nums[0]} {'minutes' if 'minuto' in q else 'seconds'}, sir.", ui)
            def _t(): time.sleep(secs); speak("Your timer has elapsed, sir.", ui)
            threading.Thread(target=_t, daemon=True).start()
        else: speak("Please specify the timer duration, sir.", ui)
        return
    if "meu ip" in q:
        try: speak(f"Your IP is {socket.gethostbyname(socket.gethostname())}, sir.", ui)
        except: speak("Unable to retrieve IP, sir.", ui)
        return
    if "sair" in q or "fechar jarvis" in q or "encerra" in q:
        speak("Shutting down JARVIS. It has been a pleasure, sir.", ui)
        time.sleep(2); QApplication.quit(); return
    speak(jarvis_response(q), ui)


# ═══════════════════════════════════════════════════════════
# VOICE RECOGNITION — inalterado
# ═══════════════════════════════════════════════════════════
def listen_loop(ui):
    if not SR_OK: ui.add_log("SpeechRecognition não instalado.", "erro"); return
    r = sr.Recognizer()
    r.energy_threshold      = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold       = 0.6
    ativo = False; t_ativo = 0; cooldown = 0.0
    ui.add_log("Microfone pronto. Diga 'JARVIS' para ativar.", "info")

    while True:
        try:
            if PG_OK and pygame.mixer.music.get_busy():
                ui.sig_state.emit("speaking"); time.sleep(0.1); continue
            else:
                ui.sig_state.emit("listening" if ativo else "idle")
            if time.time() < cooldown: time.sleep(0.1); continue
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
                speak("Yes, sir.", ui); cooldown = now + 2.5; continue
            if ativo and (now - t_ativo < 15):
                ui.sig_state.emit("processing")
                speak(jarvis_response(q), ui); cooldown = now + 2.0
                threading.Thread(target=cmd, args=(q, ui), daemon=True).start()
                t_ativo = now
            else: ativo = False
        except (sr.WaitTimeoutError, sr.UnknownValueError): pass
        except: pass


# ═══════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════
class JarvisUI(QMainWindow):

    sig_log     = Signal(str, str)
    sig_volume  = Signal(int)
    sig_stats   = Signal(dict)
    sig_cam_img = Signal(object)
    sig_gesture = Signal(str, str)  # (confirmed, raw)
    sig_state   = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S  ·  v7.0")
        self.resize(1080, 700)
        self.setMinimumSize(860, 560)
        self.setStyleSheet(GLOBAL_QSS)

        self.menu_idx  = 0
        self._cam_on   = False
        self._detector = SimpleGestureDetector()

        self._build_ui()
        self._connect_signals()

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._clock_tick)
        self._clock_timer.start(1000)

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._stats_tick)
        self._stats_timer.start(8000)

        threading.Thread(target=listen_loop, args=(self,), daemon=True).start()

    def _connect_signals(self):
        self.sig_log.connect(self._append_log)
        self.sig_volume.connect(self._vol_bar.setValue)
        self.sig_stats.connect(self._apply_stats)
        self.sig_cam_img.connect(self._update_cam_pixmap)
        self.sig_gesture.connect(self._on_gesture)
        self.sig_state.connect(self._on_state)

    # ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        main.addWidget(self._build_sidebar(), 0)
        main.addWidget(self._build_stage(),   1)

    # ─────────────────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        panel = QWidget()
        panel.setFixedWidth(260)
        panel.setStyleSheet(f"background:{DS.BG1}; border-right:1px solid {DS.BORDER_BLUE};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet(f"background:{DS.BG0}; border-bottom:1px solid {DS.BORDER_BLUE};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        logo = QLabel("J.A.R.V.I.S")
        logo.setStyleSheet(f"""
            color: {DS.BLUE_BRIGHT}; font-family: {DS.FONT_DISPLAY};
            font-size: 13px; font-weight: 700; letter-spacing: 3px; background: transparent;
        """)
        hl.addWidget(logo); hl.addStretch()
        ver = QLabel("v7.0")
        ver.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent;")
        hl.addWidget(ver)
        layout.addWidget(hdr)

        # Câmera
        cam_w = QWidget()
        cam_w.setStyleSheet("background:transparent;")
        cv  = QVBoxLayout(cam_w)
        cv.setContentsMargins(12, 12, 12, 8)
        cv.setSpacing(8)

        ch = QHBoxLayout()
        cl = QLabel("CÂMERA  /  GESTOS")
        cl.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:2px; background:transparent;")
        ch.addWidget(cl); ch.addStretch()
        self._cam_st = QLabel("● offline")
        self._cam_st.setStyleSheet(f"color:{DS.RED}; font-size:10px; font-weight:600; background:transparent;")
        ch.addWidget(self._cam_st)
        cv.addLayout(ch)

        self._cam_lbl = QLabel("Câmera inativa")
        self._cam_lbl.setAlignment(Qt.AlignCenter)
        self._cam_lbl.setFixedHeight(150)
        self._cam_lbl.setStyleSheet(f"""
            background:{DS.BG0}; color:{DS.T3}; font-size:11px;
            border:1px solid {DS.BORDER_BLUE}; border-radius:8px;
        """)
        cv.addWidget(self._cam_lbl)

        # Feedback de gesto
        self._gesture_chip = QLabel("—")
        self._gesture_chip.setAlignment(Qt.AlignCenter)
        self._gesture_chip.setFixedHeight(28)
        self._gesture_chip.setStyleSheet(f"""
            color:{DS.BLUE}; font-family:{DS.FONT_MONO}; font-size:10px; font-weight:700;
            background:{DS.BLUE_DIM}; border:1px solid {DS.BORDER_BLUE};
            border-radius:6px; letter-spacing:1.5px;
        """)
        cv.addWidget(self._gesture_chip)

        # Referência de gestos
        ref = QLabel("✋ mão aberta → ativar\n✊ punho → cancelar\n🤏 pinch → confirmar")
        ref.setStyleSheet(f"""
            color:{DS.T3}; font-size:10px; background:transparent;
            line-height: 1.6; padding: 2px 0;
        """)
        cv.addWidget(ref)

        self._cam_btn = QPushButton("▶  Ativar Câmera")
        self._cam_btn.setFixedHeight(28)
        self._cam_btn.setStyleSheet(f"""
            QPushButton {{
                background:{DS.BLUE_DIM}; color:{DS.BLUE}; border:1px solid {DS.BORDER_BLUE};
                border-radius:6px; font-size:11px; font-weight:600;
            }}
            QPushButton:hover {{ background:{DS.BLUE_MID}22; border-color:{DS.BLUE}; }}
        """)
        self._cam_btn.setCursor(Qt.PointingHandCursor)
        self._cam_btn.clicked.connect(self._toggle_cam)
        cv.addWidget(self._cam_btn)
        layout.addWidget(cam_w)

        # Sep
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{DS.BORDER_BLUE}; border:none;"); sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Log
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
        lh.addWidget(cb)
        lv.addLayout(lh)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(f"background:transparent; color:{DS.T2}; font-family:{DS.FONT_MONO}; font-size:10px; border:none;")
        lv.addWidget(self._log, 1)
        layout.addWidget(lw, 1)

        # Input
        iw = QWidget()
        iw.setStyleSheet(f"background:{DS.BG0}; border-top:1px solid {DS.BORDER_BLUE};")
        iv = QVBoxLayout(iw); iv.setContentsMargins(12, 10, 12, 12); iv.setSpacing(0)
        ir = QHBoxLayout(); ir.setSpacing(6)
        pr = QLabel("›")
        pr.setFixedWidth(14)
        pr.setStyleSheet(f"color:{DS.BLUE}; font-family:{DS.FONT_MONO}; font-size:14px; font-weight:700; background:transparent;")
        ir.addWidget(pr)
        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Digite um comando…")
        self._entry.setFixedHeight(30)
        self._entry.returnPressed.connect(self._send)
        ir.addWidget(self._entry, 1)
        sb = QPushButton("→")
        sb.setFixedSize(30, 30)
        sb.setStyleSheet(f"""
            QPushButton {{
                background:{DS.BLUE_DIM}; color:{DS.BLUE}; border:1px solid {DS.BORDER_BLUE};
                border-radius:6px; font-size:13px; font-weight:700;
            }}
            QPushButton:hover {{ background:{DS.BLUE_MID}33; border-color:{DS.BLUE}; }}
        """)
        sb.setCursor(Qt.PointingHandCursor)
        sb.clicked.connect(self._send)
        ir.addWidget(sb)
        iv.addLayout(ir)
        layout.addWidget(iw)

        return panel

    # ─────────────────────────────────────────────────────────────────
    # STAGE — área principal de voz
    # ─────────────────────────────────────────────────────────────────
    def _build_stage(self):
        stage = QWidget(); stage.setStyleSheet(f"background:{DS.BG0};")
        layout = QVBoxLayout(stage)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_top_bar())

        # Centro
        center = QWidget(); center.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.setAlignment(Qt.AlignCenter)

        cl.addStretch()

        # Network widget
        nr = QHBoxLayout(); nr.setAlignment(Qt.AlignCenter)
        self._net = NetworkWidget()
        nr.addWidget(self._net)
        cl.addLayout(nr)

        cl.addSpacing(20)

        # Status
        self._status_lbl = QLabel("AGUARDANDO COMANDO")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet(f"""
            color:{DS.BLUE_BRIGHT}; font-family:{DS.FONT_DISPLAY};
            font-size:12px; font-weight:700; letter-spacing:5px; background:transparent;
        """)
        cl.addWidget(self._status_lbl)

        cl.addSpacing(6)

        self._sub_lbl = QLabel("Diga 'JARVIS' para ativar")
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setStyleSheet(f"color:{DS.T3}; font-family:{DS.FONT_MONO}; font-size:11px; letter-spacing:1px; background:transparent;")
        cl.addWidget(self._sub_lbl)

        cl.addStretch()

        layout.addWidget(center, 1)
        layout.addWidget(self._build_bottom_bar())

        return stage

    # ─────────────────────────────────────────────────────────────────
    def _build_top_bar(self):
        bar = QWidget(); bar.setFixedHeight(46)
        bar.setStyleSheet(f"background:{DS.BG1}; border-bottom:1px solid {DS.BORDER_BLUE};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        self._clock_lbl = QLabel("00:00:00")
        self._clock_lbl.setStyleSheet(f"""
            color:{DS.BLUE_BRIGHT}; font-family:{DS.FONT_DISPLAY};
            font-size:15px; font-weight:700; letter-spacing:2px; background:transparent;
        """)
        layout.addWidget(self._clock_lbl)

        self._date_lbl = QLabel("")
        self._date_lbl.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent; letter-spacing:1px;")
        layout.addWidget(self._date_lbl)

        layout.addStretch()

        # Volume
        vr = QHBoxLayout(); vr.setSpacing(6)
        vl = QLabel("VOL")
        vl.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:1px; background:transparent;")
        vr.addWidget(vl)
        self._vol_bar = QProgressBar()
        self._vol_bar.setRange(0, 100); self._vol_bar.setValue(50)
        self._vol_bar.setFixedSize(60, 3); self._vol_bar.setTextVisible(False)
        self._vol_bar.setStyleSheet(f"""
            QProgressBar {{ background:{DS.BG0}; border:none; border-radius:2px; }}
            QProgressBar::chunk {{ background:{DS.BLUE}; border-radius:2px; }}
        """)
        vr.addWidget(self._vol_bar)
        layout.addLayout(vr)

        mic = QPushButton("🎙")
        mic.setFixedSize(32, 32)
        mic.setToolTip("Microfone ativo — diga 'JARVIS'")
        mic.setStyleSheet(f"""
            QPushButton {{
                background:{DS.BLUE_DIM}; color:{DS.BLUE}; border:1px solid {DS.BORDER_BLUE};
                border-radius:16px; font-size:13px;
            }}
            QPushButton:hover {{ background:{DS.BLUE_MID}44; border-color:{DS.BLUE}; }}
        """)
        mic.setCursor(Qt.PointingHandCursor)
        mic.clicked.connect(lambda: speak("Yes, sir.", self))
        layout.addWidget(mic)

        return bar

    def _build_bottom_bar(self):
        bar = QWidget(); bar.setFixedHeight(40)
        bar.setStyleSheet(f"background:{DS.BG1}; border-top:1px solid {DS.BORDER_BLUE};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        self._sb_dot = QLabel("●")
        self._sb_dot.setStyleSheet(f"color:{DS.GREEN}; font-size:8px; background:transparent;")
        layout.addWidget(self._sb_dot)
        self._sb_lbl = QLabel("  Sistema online")
        self._sb_lbl.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent;")
        layout.addWidget(self._sb_lbl)

        layout.addStretch()

        self._stat_labels = {}
        for i, (k, key) in enumerate([("CPU","cpu"),("RAM","ram"),("DISCO","disk"),("BAT","bat")]):
            if i > 0:
                sep = QLabel("|"); sep.setStyleSheet(f"color:{DS.BORDER_BLUE}; background:transparent; padding: 0 8px;")
                layout.addWidget(sep)
            rw = QHBoxLayout(); rw.setSpacing(4)
            kl = QLabel(k); kl.setStyleSheet(f"color:{DS.T3}; font-size:9px; font-weight:700; letter-spacing:1px; background:transparent;")
            rw.addWidget(kl)
            vl = QLabel("—"); vl.setStyleSheet(f"color:{DS.BLUE}; font-family:{DS.FONT_MONO}; font-size:10px; font-weight:700; background:transparent;")
            rw.addWidget(vl)
            self._stat_labels[key] = vl
            layout.addLayout(rw)

        return bar

    # ═════════════════════════════════════════════════════════════════
    # ESTADO / GESTO
    # ═════════════════════════════════════════════════════════════════
    def _on_state(self, state: str):
        self._net.set_state(state)
        cfg = {
            "idle":       ("AGUARDANDO COMANDO",   "Diga 'JARVIS' para ativar",  DS.BLUE_BRIGHT),
            "listening":  ("OUVINDO",               "Escutando você…",            DS.CYAN),
            "processing": ("PROCESSANDO",           "Analisando comando…",        DS.BLUE),
            "speaking":   ("RESPONDENDO",           "JARVIS falando…",            DS.BLUE_BRIGHT),
        }.get(state, ("AGUARDANDO COMANDO", "Diga 'JARVIS' para ativar", DS.BLUE_BRIGHT))

        main_txt, sub_txt, color = cfg
        self._status_lbl.setText(main_txt)
        self._status_lbl.setStyleSheet(f"""
            color:{color}; font-family:{DS.FONT_DISPLAY};
            font-size:12px; font-weight:700; letter-spacing:5px; background:transparent;
        """)
        self._sub_lbl.setText(sub_txt)

    def _on_gesture(self, confirmed: str, raw: str):
        """Processa gesto confirmado e atualiza chip visual."""
        label_map = {
            SimpleGestureDetector.OPEN_PALM: "✋  MÃO ABERTA",
            SimpleGestureDetector.FIST:      "✊  PUNHO",
            SimpleGestureDetector.PINCH:     "🤏  PINCH",
        }
        # Chip visual (mostra raw para feedback imediato)
        raw_label = label_map.get(raw, "—")
        self._gesture_chip.setText(raw_label if raw != SimpleGestureDetector.NONE else "—")

        if not confirmed or confirmed == SimpleGestureDetector.NONE:
            return

        # ── Ações por gesto confirmado ─────────────────────────────────
        if confirmed == SimpleGestureDetector.OPEN_PALM:
            # Ativar / chamar atenção
            self.add_log("Gesto: MÃO ABERTA → ativando Jarvis", "gesto")
            speak("Listening, sir.", self)
            self.sig_state.emit("listening")

        elif confirmed == SimpleGestureDetector.FIST:
            # Cancelar / parar fala
            self.add_log("Gesto: PUNHO → cancelar", "gesto")
            if PG_OK:
                try: pygame.mixer.music.stop()
                except: pass
            speak("Command cancelled, sir.", self)

        elif confirmed == SimpleGestureDetector.PINCH:
            # Confirmar último item do menu
            self.add_log("Gesto: PINCH → confirmar", "gesto")
            self.menu_confirm()

    # ═════════════════════════════════════════════════════════════════
    # CÂMERA
    # ═════════════════════════════════════════════════════════════════
    def _toggle_cam(self):
        if not CV2_OK: self.add_log("mediapipe/opencv não instalado", "erro"); return
        if not self._cam_on: self._start_cam()
        else: self._stop_cam()

    def _start_cam(self):
        if not self._detector.start():
            self.add_log("Webcam não encontrada", "erro"); return
        self._cam_on = True
        self._cam_btn.setText("■  Parar câmera")
        self._cam_btn.setStyleSheet(f"""
            QPushButton {{
                background:{DS.RED}22; color:{DS.RED}; border:1px solid {DS.RED}66;
                border-radius:6px; font-size:11px; font-weight:600;
            }}
            QPushButton:hover {{ background:{DS.RED}44; }}
        """)
        self._cam_st.setText("● ao vivo")
        self._cam_st.setStyleSheet(f"color:{DS.GREEN}; font-size:10px; font-weight:600; background:transparent;")
        self._sb_lbl.setText("  Câmera ativa — gestos habilitados")
        self._sb_lbl.setStyleSheet(f"color:{DS.GREEN}; font-size:10px; background:transparent;")
        self.add_log("Câmera ativada — 3 gestos disponíveis", "gesto")
        speak("Camera activated. Gesture control is now online, sir.", self)
        threading.Thread(target=self._cam_loop, daemon=True).start()

    def _stop_cam(self):
        self._cam_on = False; self._detector.stop()
        self._cam_btn.setText("▶  Ativar Câmera")
        self._cam_btn.setStyleSheet(f"""
            QPushButton {{
                background:{DS.BLUE_DIM}; color:{DS.BLUE}; border:1px solid {DS.BORDER_BLUE};
                border-radius:6px; font-size:11px; font-weight:600;
            }}
            QPushButton:hover {{ background:{DS.BLUE_MID}22; border-color:{DS.BLUE}; }}
        """)
        self._cam_st.setText("● offline")
        self._cam_st.setStyleSheet(f"color:{DS.RED}; font-size:10px; font-weight:600; background:transparent;")
        self._cam_lbl.clear(); self._cam_lbl.setText("Câmera inativa")
        self._gesture_chip.setText("—")
        self._sb_lbl.setText("  Sistema online")
        self._sb_lbl.setStyleSheet(f"color:{DS.T3}; font-size:10px; background:transparent;")
        self.add_log("Câmera desativada", "info")
        speak("Camera deactivated, sir.", self)

    def _cam_loop(self):
        while self._cam_on:
            frame, confirmed, raw = self._detector.read()
            if frame is None: time.sleep(0.04); continue
            self.sig_gesture.emit(confirmed or "", raw or "")
            try:
                sm = cv2.resize(frame, (236, 148))
                self.sig_cam_img.emit(sm)
            except: pass
            time.sleep(0.025)

    def _update_cam_pixmap(self, frame_bgr):
        try:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self._cam_lbl.setPixmap(QPixmap.fromImage(img).scaled(
                self._cam_lbl.width(), self._cam_lbl.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            self._cam_lbl.setText("")
        except: pass

    # ═════════════════════════════════════════════════════════════════
    # MENU (mantido para compatibilidade com gesto PINCH)
    # ═════════════════════════════════════════════════════════════════
    def refresh_menu(self): pass

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

    # ═════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═════════════════════════════════════════════════════════════════
    def update_stats(self, info): self.sig_stats.emit(info)
    def _apply_stats(self, info):
        for k, lbl in self._stat_labels.items():
            if k in info: lbl.setText(info[k])

    def set_volume(self, pct): self.sig_volume.emit(pct)
    def highlight_mode(self, _): pass  # compatibilidade

    def add_log(self, text, tag=""):
        self.sig_log.emit(text, tag)

    def _append_log(self, text, tag):
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

        if tag == "jarvis": self.sig_state.emit("speaking")
        elif tag == "user": self.sig_state.emit("processing")

    def _send(self):
        q = self._entry.text().strip()
        if not q: return
        self._entry.clear()
        self.add_log(f"YOU › {q}", "user")
        speak(jarvis_response(q), self)
        threading.Thread(target=cmd, args=(q, self), daemon=True).start()

    def _run(self, action):
        if callable(action): threading.Thread(target=action, daemon=True).start()
        else:
            self.add_log(f"CMD › {action}", "user")
            speak(jarvis_response(action), self)
            threading.Thread(target=cmd, args=(action, self), daemon=True).start()

    def _clock_tick(self):
        n = datetime.datetime.now()
        self._clock_lbl.setText(n.strftime("%H:%M:%S"))
        self._date_lbl.setText(n.strftime("%d/%m · %a").upper())

    def _stats_tick(self):
        self.update_stats(sys_info())

    def run(self):
        self.add_log("Inicializando…", "info")
        def _boot():
            _speak_ready.wait(timeout=15)
            speak("JARVIS online. All modules loaded. Ready for your command, sir.", self)
        threading.Thread(target=_boot, daemon=True).start()
        self.show()


# ═══════════════════════════════════════════════════════════
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
