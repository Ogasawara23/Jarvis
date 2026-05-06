"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                J.A.R.V.I.S  —  TELA DE BOOT  v1.0                         ║
║           Animação de inicialização com Reator ARC                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Dependências: PySide6                                                       ║
║  Uso: Chamado automaticamente pelo launcher principal (jarvis_launcher.py)  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import math
import time

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore    import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui     import (
    QPainter, QColor, QPen, QBrush, QFont,
    QRadialGradient, QConicalGradient, QLinearGradient,
    QFontDatabase, QPainterPath,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE ESTILO
# ═══════════════════════════════════════════════════════════════════════════════
AZUL_NEON  = QColor(0,   170, 255)       # azul brilhante
CIANO      = QColor(0,   230, 255)       # ciano elétrico
BRANCO     = QColor(220, 240, 255)       # branco frio
ROXO_DIM   = QColor(80,   40, 160, 80)  # roxo suave (acento)
PRETO      = QColor(3,     8,  16)       # fundo escuro

# Sequência de textos que aparecem durante o boot
MENSAGENS_BOOT = [
    "Inicializando sistema...",
    "Carregando módulos de IA...",
    "Verificando integridade dos dados...",
    "Sincronizando redes neurais...",
    "Acesso ao núcleo autorizado...",
    "J.A.R.V.I.S  ONLINE",
]

# Duração total do boot em milissegundos
DURACAO_BOOT_MS = 4500


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET DO REATOR ARC
# ═══════════════════════════════════════════════════════════════════════════════
class ReatorARC(QWidget):
    """
    Widget que desenha e anima o Reator ARC estilo JARVIS.
    Composto por:
      - Núcleo central com gradiente radial pulsante
      - Anéis concêntricos rotacionando em velocidades diferentes
      - Arcos de energia externos
      - Partículas de plasma girando ao redor
      - Brilho difuso dinâmico
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ── Estado da animação ─────────────────────────────────────────────
        self._t          = 0.0    # tempo acumulado (em ticks)
        self._pulso      = 0.0    # fase da pulsação central
        self._anel1_ang  = 0.0    # ângulo do anel 1 (externo)
        self._anel2_ang  = 0.0    # ângulo do anel 2 (médio)
        self._anel3_ang  = 0.0    # ângulo do anel 3 (interno)
        self._energia    = 0.0    # 0.0 → 1.0 (nível de energia durante a abertura)

        # ── Timer principal (60 fps) ───────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)      # ~60 fps

    # ── Loop de animação ───────────────────────────────────────────────────
    def _tick(self):
        self._t         += 0.016
        self._pulso      = (self._pulso  + 0.055) % (2 * math.pi)
        self._anel1_ang  = (self._anel1_ang + 0.8)  % 360
        self._anel2_ang  = (self._anel2_ang - 1.2)  % 360   # sentido contrário
        self._anel3_ang  = (self._anel3_ang + 2.1)  % 360
        # Energia aumenta gradualmente até 1.0 em ~2 segundos
        self._energia    = min(1.0, self._energia + 0.005)
        self.update()

    # ── Renderização ───────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h   = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        E      = self._energia                          # 0.0 → 1.0
        pulso  = math.sin(self._pulso)                  # -1.0 → 1.0

        # ── 1. BRILHO DIFUSO DE FUNDO ──────────────────────────────────────
        glow_r = 140 * E
        glow   = QRadialGradient(cx, cy, glow_r)
        glow.setColorAt(0.0, QColor(0, 150, 255, int(60 * E)))
        glow.setColorAt(0.5, QColor(0,  80, 200, int(25 * E)))
        glow.setColorAt(1.0, QColor(0,   0,   0,  0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # ── 2. ANEL EXTERNO (giratório, segmentado) ────────────────────────
        self._desenha_anel_segmentado(
            painter, cx, cy,
            raio=120, espessura=2,
            angulo_base=self._anel1_ang,
            segmentos=12, gap=0.3,
            alpha=int(180 * E),
            cor_base=AZUL_NEON,
        )

        # ── 3. MARCAÇÕES CARDIAIS (N/S/L/O) ───────────────────────────────
        self._desenha_marcacoes(painter, cx, cy, raio=108, alpha=int(120 * E))

        # ── 4. ANEL MÉDIO (sentido contrário, hexagonal) ───────────────────
        self._desenha_anel_segmentado(
            painter, cx, cy,
            raio=90, espessura=1.5,
            angulo_base=self._anel2_ang,
            segmentos=6, gap=0.4,
            alpha=int(200 * E),
            cor_base=CIANO,
        )

        # ── 5. ANEL INTERNO (rápido, fino) ────────────────────────────────
        self._desenha_anel_segmentado(
            painter, cx, cy,
            raio=68, espessura=1,
            angulo_base=self._anel3_ang,
            segmentos=8, gap=0.2,
            alpha=int(160 * E),
            cor_base=AZUL_NEON,
        )

        # ── 6. ARCOS DE ENERGIA (estilo capacitor) ────────────────────────
        self._desenha_arcos_energia(painter, cx, cy, E, pulso)

        # ── 7. PARTÍCULAS ORBITAIS ─────────────────────────────────────────
        self._desenha_particulas(painter, cx, cy, E)

        # ── 8. HEXÁGONO CENTRAL ───────────────────────────────────────────
        self._desenha_hexagono(painter, cx, cy, raio=42, E=E, pulso=pulso)

        # ── 9. NÚCLEO CENTRAL (pulsante) ──────────────────────────────────
        core_r = 28 + 4 * abs(pulso) * E
        core_g = QRadialGradient(cx, cy, core_r * 2.5)
        a0     = int((200 + 55 * abs(pulso)) * E)
        core_g.setColorAt(0.0, QColor(255, 255, 255, a0))
        core_g.setColorAt(0.3, QColor(100, 220, 255, int(220 * E)))
        core_g.setColorAt(0.7, QColor(0,   150, 255, int(150 * E)))
        core_g.setColorAt(1.0, QColor(0,    50, 150,  0))
        painter.setBrush(QBrush(core_g))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), core_r * 2.5, core_r * 2.5)

        # Ponto brilhante central
        painter.setBrush(QBrush(QColor(220, 245, 255, int(255 * E))))
        painter.drawEllipse(QPointF(cx, cy), core_r * 0.35, core_r * 0.35)

        painter.end()

    # ── Auxiliares de desenho ──────────────────────────────────────────────

    def _desenha_anel_segmentado(
        self, painter, cx, cy,
        raio, espessura, angulo_base,
        segmentos, gap, alpha, cor_base
    ):
        """Desenha um anel formado por segmentos de arco com espaçamento."""
        passo = 360.0 / segmentos
        for i in range(segmentos):
            ang_ini = angulo_base + i * passo
            comprimento = passo * (1.0 - gap)
            # Varia alpha por posição para dar profundidade
            a_var = int(alpha * (0.5 + 0.5 * math.cos(math.radians(ang_ini))))
            cor = QColor(cor_base)
            cor.setAlpha(max(0, a_var))
            pen = QPen(cor, espessura)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            rect = QRectF(cx - raio, cy - raio, raio * 2, raio * 2)
            painter.drawArc(rect,
                            int(ang_ini * 16),
                            int(comprimento * 16))

    def _desenha_marcacoes(self, painter, cx, cy, raio, alpha):
        """Pequenas marcações nos 4 pontos cardeais do anel externo."""
        for ang in [0, 90, 180, 270]:
            rad = math.radians(ang)
            x1  = cx + raio * math.cos(rad)
            y1  = cy + raio * math.sin(rad)
            x2  = cx + (raio + 10) * math.cos(rad)
            y2  = cy + (raio + 10) * math.sin(rad)
            cor = QColor(CIANO); cor.setAlpha(alpha)
            pen = QPen(cor, 2, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _desenha_arcos_energia(self, painter, cx, cy, E, pulso):
        """Arcos de descarga de energia ao redor do hexágono central."""
        n_arcos = 3
        for i in range(n_arcos):
            fase   = (self._t * 2.5 + i * (2 * math.pi / n_arcos)) % (2 * math.pi)
            raio_a = 55 + 8 * math.sin(fase)
            ang    = math.degrees(fase)
            comp   = 25 + 15 * abs(math.sin(fase * 1.3))
            a      = int(160 * E * (0.5 + 0.5 * abs(math.sin(fase))))
            cor    = QColor(CIANO); cor.setAlpha(a)
            pen    = QPen(cor, 2.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            rect = QRectF(cx - raio_a, cy - raio_a, raio_a * 2, raio_a * 2)
            painter.drawArc(rect, int(ang * 16), int(comp * 16))

    def _desenha_particulas(self, painter, cx, cy, E):
        """Partículas de plasma em órbita."""
        n = 8
        for i in range(n):
            fase   = self._t * 1.8 + i * (2 * math.pi / n)
            raio   = 78 + 6 * math.sin(fase * 2.3)
            px     = cx + raio * math.cos(fase)
            py     = cy + raio * math.sin(fase)
            a      = int(200 * E * (0.4 + 0.6 * abs(math.sin(fase))))
            sz     = 2.5 + 1.5 * abs(math.sin(fase))
            g      = QRadialGradient(px, py, sz * 3)
            gc     = QColor(CIANO); gc.setAlpha(a // 3)
            g.setColorAt(0.0, gc); g.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(g))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), sz * 3, sz * 3)
            pc = QColor(CIANO); pc.setAlpha(a)
            painter.setBrush(QBrush(pc))
            painter.drawEllipse(QPointF(px, py), sz, sz)

    def _desenha_hexagono(self, painter, cx, cy, raio, E, pulso):
        """Hexágono central com borda brilhante."""
        path = QPainterPath()
        for i in range(6):
            ang = math.radians(60 * i - 30)
            px  = cx + raio * math.cos(ang)
            py  = cy + raio * math.sin(ang)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()

        # Preenchimento sutil
        fill_alpha = int(30 * E)
        painter.setBrush(QBrush(QColor(0, 180, 255, fill_alpha)))
        # Borda hexagonal
        borda_alpha = int((160 + 60 * abs(pulso)) * E)
        cor_borda   = QColor(CIANO); cor_borda.setAlpha(borda_alpha)
        painter.setPen(QPen(cor_borda, 1.5))
        painter.drawPath(path)


# ═══════════════════════════════════════════════════════════════════════════════
# TELA DE BOOT COMPLETA
# ═══════════════════════════════════════════════════════════════════════════════
class BootScreen(QWidget):
    """
    Janela de inicialização do JARVIS.
    Emite o sinal `boot_concluido` quando a animação termina.
    """
    boot_concluido = Signal()

    def __init__(self):
        super().__init__()
        self._configurar_janela()
        self._construir_interface()
        self._iniciar_sequencia()

    # ── Configuração da janela ─────────────────────────────────────────────
    def _configurar_janela(self):
        self.setWindowTitle("J.A.R.V.I.S")
        self.setFixedSize(700, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Centraliza na tela
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

    # ── Construção da UI ───────────────────────────────────────────────────
    def _construir_interface(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container principal (fundo com borda)
        self._container = QWidget(self)
        self._container.setStyleSheet("""
            QWidget {
                background-color: rgba(3, 8, 16, 245);
                border: 1px solid rgba(0, 170, 255, 80);
                border-radius: 12px;
            }
        """)
        layout.addWidget(self._container)

        vl = QVBoxLayout(self._container)
        vl.setContentsMargins(30, 30, 30, 30)
        vl.setSpacing(0)
        vl.setAlignment(Qt.AlignCenter)

        # ── Título superior ────────────────────────────────────────────────
        titulo = QLabel("J.A.R.V.I.S")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            color: rgba(0, 200, 255, 240);
            font-family: 'Orbitron', 'Consolas', monospace;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 12px;
            background: transparent;
        """)
        vl.addWidget(titulo)

        subtitulo = QLabel("SISTEMA DE ASSISTÊNCIA AVANÇADO")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("""
            color: rgba(0, 120, 180, 200);
            font-family: 'Consolas', monospace;
            font-size: 10px;
            letter-spacing: 5px;
            background: transparent;
            margin-bottom: 20px;
        """)
        vl.addWidget(subtitulo)

        # ── Reator ARC central ─────────────────────────────────────────────
        row = QVBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        self._reator = ReatorARC()
        row.addWidget(self._reator, alignment=Qt.AlignCenter)
        vl.addLayout(row)

        # ── Texto de status (mensagens sequenciais) ────────────────────────
        self._lbl_status = QLabel("Inicializando sistema...")
        self._lbl_status.setAlignment(Qt.AlignCenter)
        self._lbl_status.setStyleSheet("""
            color: rgba(0, 180, 255, 230);
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            letter-spacing: 2px;
            background: transparent;
            margin-top: 18px;
            min-height: 24px;
        """)
        vl.addWidget(self._lbl_status)

        # ── Barra de progresso customizada ────────────────────────────────
        self._barra = BarraProgresso()
        self._barra.setFixedSize(400, 4)
        vl.addWidget(self._barra, alignment=Qt.AlignCenter)
        vl.addSpacing(8)

        # ── Rodapé com versão ──────────────────────────────────────────────
        rodape = QLabel("v8.1  ·  MÓDULOS CARREGADOS: 0/6")
        rodape.setObjectName("rodape")
        rodape.setAlignment(Qt.AlignCenter)
        rodape.setStyleSheet("""
            color: rgba(0, 80, 120, 180);
            font-family: 'Consolas', monospace;
            font-size: 9px;
            letter-spacing: 3px;
            background: transparent;
        """)
        vl.addWidget(rodape)
        self._lbl_rodape = rodape

    # ── Sequência de boot ─────────────────────────────────────────────────
    def _iniciar_sequencia(self):
        """Programa a exibição das mensagens e o progresso."""
        self._msg_idx   = 0
        self._progresso = 0.0

        total_msgs = len(MENSAGENS_BOOT)
        intervalo  = DURACAO_BOOT_MS // total_msgs  # ms entre mensagens

        # Timer de mensagens
        self._timer_msg = QTimer(self)
        self._timer_msg.timeout.connect(self._proxima_mensagem)
        self._timer_msg.start(intervalo)

        # Timer de progresso suave (atualiza a cada 50ms)
        self._passo_prog = 1.0 / (DURACAO_BOOT_MS / 50)
        self._timer_prog = QTimer(self)
        self._timer_prog.timeout.connect(self._avanca_progresso)
        self._timer_prog.start(50)

    def _proxima_mensagem(self):
        """Avança para a próxima mensagem de boot."""
        if self._msg_idx < len(MENSAGENS_BOOT):
            texto = MENSAGENS_BOOT[self._msg_idx]
            self._lbl_status.setText(texto)
            self._lbl_rodape.setText(
                f"v8.1  ·  MÓDULOS CARREGADOS: {self._msg_idx + 1}/{len(MENSAGENS_BOOT)}"
            )

            # Última mensagem → estiliza diferente e encerra
            if self._msg_idx == len(MENSAGENS_BOOT) - 1:
                self._lbl_status.setStyleSheet("""
                    color: rgba(0, 255, 200, 255);
                    font-family: 'Orbitron', 'Consolas', monospace;
                    font-size: 15px;
                    font-weight: 700;
                    letter-spacing: 5px;
                    background: transparent;
                    margin-top: 18px;
                    min-height: 24px;
                """)
                self._timer_msg.stop()
                # Aguarda 800ms e emite o sinal de conclusão
                QTimer.singleShot(800, self._finalizar)

            self._msg_idx += 1

    def _avanca_progresso(self):
        """Incrementa a barra de progresso suavemente."""
        self._progresso = min(1.0, self._progresso + self._passo_prog)
        self._barra.set_progresso(self._progresso)
        if self._progresso >= 1.0:
            self._timer_prog.stop()

    def _finalizar(self):
        """Fecha a tela de boot e emite o sinal para abrir o login."""
        self.close()
        self.boot_concluido.emit()

    # ── Permite arrastar a janela sem barra de título ──────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)


# ═══════════════════════════════════════════════════════════════════════════════
# BARRA DE PROGRESSO CUSTOMIZADA
# ═══════════════════════════════════════════════════════════════════════════════
class BarraProgresso(QWidget):
    """Barra de progresso futurista desenhada manualmente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._progresso = 0.0   # 0.0 → 1.0
        self._t         = 0.0
        timer = QTimer(self); timer.timeout.connect(self._tick); timer.start(30)

    def _tick(self):
        self._t += 0.05
        self.update()

    def set_progresso(self, valor: float):
        self._progresso = max(0.0, min(1.0, valor))
        self.update()

    def paintEvent(self, event):
        if self._progresso <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        fill = int(w * self._progresso)

        # Trilha de fundo
        painter.setBrush(QBrush(QColor(0, 40, 80, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, h // 2, h // 2)

        if fill > 0:
            # Gradiente da barra
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor(0,  120, 220))
            grad.setColorAt(0.6, QColor(0,  200, 255))
            grad.setColorAt(1.0, QColor(150, 240, 255))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(0, 0, fill, h, h // 2, h // 2)

            # Brilho na ponta
            brilho_x = fill - 6
            if brilho_x > 0:
                brilho = QRadialGradient(brilho_x, h // 2, 8)
                brilho.setColorAt(0.0, QColor(255, 255, 255, 200))
                brilho.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(brilho))
                painter.drawEllipse(brilho_x - 8, -4, 16, h + 8)

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════════
# TESTE ISOLADO
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    boot = BootScreen()
    boot.boot_concluido.connect(lambda: print("Boot concluído!"))
    boot.show()
    sys.exit(app.exec())
