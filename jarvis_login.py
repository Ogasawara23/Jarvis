"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                J.A.R.V.I.S  —  TELA DE LOGIN  v1.0                        ║
║           Interface de autenticação futurista                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Dependências: PySide6                                                       ║
║  Uso: Chamado automaticamente pelo launcher principal (jarvis_launcher.py)  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SISTEMA DE CREDENCIAIS:                                                     ║
║  • Armazenamento em JSON local cifrado com hash SHA-256                     ║
║  • Arquivo: jarvis_auth.json (criado automaticamente na 1ª execução)        ║
║  • Credenciais padrão: usuário "stark" / senha "jarvis123"                  ║
║  • Função de primeiro acesso cria o hash e salva                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import math
import json
import hashlib
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect,
)
from PySide6.QtCore    import Qt, QTimer, QPointF, QRectF, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui     import (
    QPainter, QColor, QPen, QBrush, QFont,
    QRadialGradient, QLinearGradient, QPainterPath,
    QPixmap, QImage,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

# Arquivo de autenticação local (criado ao lado do script)
AUTH_FILE = Path(__file__).parent / "jarvis_auth.json"

# Credenciais padrão (usadas na criação inicial)
USUARIO_PADRAO = "Vinicius Ogasawara"
SENHA_PADRAO   = "squerdista123"

# Tempo para auto-fechar mensagem de feedback (ms)
TEMPO_FEEDBACK_MS = 2500

# Cores
AZUL_NEON  = "#00AAFF"
CIANO      = "#00E6FF"
VERDE_OK   = "#00E5A0"
VERMELHO   = "#FF3358"
PRETO_BG   = "#030810"
AZUL_ESCURO= "#060D1A"
BORDA_AZUL = "#0D3060"


# ═══════════════════════════════════════════════════════════════════════════════
# GERENCIADOR DE AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
class GerenciadorAuth:
    """
    Gerencia credenciais e sessões.
    • Senhas armazenadas como SHA-256 (nunca em texto plano)
    • Sessão salva como token no JSON (evita re-login)
    """

    def __init__(self):
        self._dados = self._carregar()
        # Cria arquivo com usuário padrão se não existir
        if not AUTH_FILE.exists() or "usuarios" not in self._dados:
            self._criar_usuario_padrao()

    # ── Persistência ──────────────────────────────────────────────────────
    def _carregar(self) -> dict:
        try:
            if AUTH_FILE.exists():
                with open(AUTH_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _salvar(self):
        try:
            with open(AUTH_FILE, "w", encoding="utf-8") as f:
                json.dump(self._dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Auth] Erro ao salvar: {e}")

    # ── Usuário padrão ────────────────────────────────────────────────────
    def _criar_usuario_padrao(self):
        self._dados = {
            "usuarios": {
                USUARIO_PADRAO: self._hash(SENHA_PADRAO)
            },
            "sessao": None,
        }
        self._salvar()

    # ── Hash ──────────────────────────────────────────────────────────────
    @staticmethod
    def _hash(texto: str) -> str:
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    # ── API Pública ───────────────────────────────────────────────────────
    def verificar_login(self, usuario: str, senha: str) -> bool:
        """Retorna True se as credenciais estiverem corretas."""
        usuarios = self._dados.get("usuarios", {})
        hash_correto = usuarios.get(usuario.lower().strip())
        if not hash_correto:
            return False
        return hash_correto == self._hash(senha)

    def salvar_sessao(self, usuario: str):
        """Marca sessão como ativa (evita re-login)."""
        token = self._hash(usuario + "sessao_ativa")
        self._dados["sessao"] = {"usuario": usuario, "token": token}
        self._salvar()

    def sessao_ativa(self) -> str | None:
        """Retorna o nome do usuário logado ou None."""
        sessao = self._dados.get("sessao")
        if not sessao:
            return None
        usuario = sessao.get("usuario", "")
        token   = sessao.get("token", "")
        if token == self._hash(usuario + "sessao_ativa"):
            return usuario
        return None

    def encerrar_sessao(self):
        """Remove a sessão salva."""
        self._dados["sessao"] = None
        self._salvar()

    def cadastrar_usuario(self, usuario: str, senha: str):
        """Cadastra um novo usuário (para uso futuro)."""
        if "usuarios" not in self._dados:
            self._dados["usuarios"] = {}
        self._dados["usuarios"][usuario.lower().strip()] = self._hash(senha)
        self._salvar()


# ═══════════════════════════════════════════════════════════════════════════════
# WIDGET DE FUNDO ANIMADO
# ═══════════════════════════════════════════════════════════════════════════════
class FundoAnimado(QWidget):
    """
    Camada de fundo com grade de linhas e partículas flutuantes,
    criando o efeito de 'malha de dados' futurista.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = 0.0
        self._particulas = [
            {
                "x": math.random_val if False else __import__("random").uniform(0, 1),
                "y": __import__("random").uniform(0, 1),
                "vx": __import__("random").uniform(-0.0002, 0.0002),
                "vy": __import__("random").uniform(-0.0003, 0.0003),
                "alpha": __import__("random").uniform(0.2, 0.8),
                "r": __import__("random").uniform(1, 3),
            }
            for _ in range(30)
        ]
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)     # ~30 fps (fundo não precisa de 60)

    def _tick(self):
        self._t += 0.016
        for p in self._particulas:
            p["x"] = (p["x"] + p["vx"]) % 1.0
            p["y"] = (p["y"] + p["vy"]) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # ── Grade de pontos ────────────────────────────────────────────────
        passo = 40
        for gx in range(0, w + passo, passo):
            for gy in range(0, h + passo, passo):
                fase = math.sin(self._t * 0.5 + gx * 0.02 + gy * 0.02)
                a    = int(15 + 10 * fase)
                c    = QColor(0, 100, 180, max(0, a))
                painter.setBrush(QBrush(c))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(gx, gy), 1, 1)

        # ── Linhas da grade ────────────────────────────────────────────────
        cor_linha = QColor(0, 60, 120, 25)
        pen = QPen(cor_linha, 0.5)
        painter.setPen(pen)
        for gx in range(0, w + passo, passo):
            painter.drawLine(gx, 0, gx, h)
        for gy in range(0, h + passo, passo):
            painter.drawLine(0, gy, w, gy)

        # ── Partículas flutuantes ─────────────────────────────────────────
        painter.setPen(Qt.NoPen)
        for p in self._particulas:
            px   = p["x"] * w
            py   = p["y"] * h
            fase = math.sin(self._t * 1.5 + px * 0.01)
            a    = int(180 * p["alpha"] * (0.5 + 0.5 * fase))
            c    = QColor(0, 180, 255, max(0, a))
            g    = QRadialGradient(px, py, p["r"] * 4)
            gc   = QColor(c); gc.setAlpha(a // 3)
            g.setColorAt(0.0, gc); g.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(px, py), p["r"] * 4, p["r"] * 4)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(px, py), p["r"], p["r"])

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════════
# BOTÃO FUTURISTA CUSTOMIZADO
# ═══════════════════════════════════════════════════════════════════════════════
class BotaoFuturista(QPushButton):
    """
    Botão com efeito de brilho no hover e animação de clique.
    """

    def __init__(self, texto: str, cor: str = AZUL_NEON, parent=None):
        super().__init__(texto, parent)
        self._cor       = cor
        self._hover     = False
        self._pulsando  = False
        self._t         = 0.0
        self.setFixedHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(30)

    def _tick(self):
        self._t += 0.06
        if self._hover or self._pulsando:
            self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cor  = QColor(self._cor)

        # Fator de brilho baseado em hover/animação
        if self._hover:
            brilho = 0.7 + 0.3 * abs(math.sin(self._t * 3))
        else:
            brilho = 0.25 + 0.15 * abs(math.sin(self._t))

        # Fundo do botão
        bg_alpha = int(brilho * 60)
        fundo    = QColor(cor.red(), cor.green(), cor.blue(), bg_alpha)
        painter.setBrush(QBrush(fundo))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 6, 6)

        # Borda brilhante
        borda_alpha = int(brilho * 220)
        borda_cor   = QColor(cor.red(), cor.green(), cor.blue(), borda_alpha)
        painter.setPen(QPen(borda_cor, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(1, 1, w - 2, h - 2, 5, 5)

        # Linha de destaque no topo (chanfro superior)
        if self._hover:
            shine_grad = QLinearGradient(0, 0, w, 0)
            shine_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
            shine_grad.setColorAt(0.5, QColor(255, 255, 255, int(brilho * 80)))
            shine_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(QPen(QBrush(shine_grad), 1))
            painter.drawLine(8, 1, w - 8, 1)

        # Texto
        painter.setPen(QPen(QColor(cor.red(), cor.green(), cor.blue(),
                                   int(200 + 55 * brilho))))
        font = QFont("Orbitron, Consolas", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, w, h, Qt.AlignCenter, self.text())

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════════
# CAMPO DE TEXTO FUTURISTA
# ═══════════════════════════════════════════════════════════════════════════════
ESTILO_CAMPO = f"""
QLineEdit {{
    background: rgba(6, 13, 26, 200);
    color: {AZUL_NEON};
    border: 1px solid {BORDA_AZUL};
    border-radius: 6px;
    padding: 0 14px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: rgba(0, 100, 200, 100);
}}
QLineEdit:focus {{
    border-color: {CIANO};
    background: rgba(0, 20, 50, 230);
}}
QLineEdit::placeholder {{
    color: rgba(0, 80, 120, 180);
}}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TELA DE LOGIN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
class LoginScreen(QWidget):
    """
    Tela de login futurista do JARVIS.
    Emite `login_aprovado(usuario)` em caso de sucesso.
    """
    login_aprovado = Signal(str)

    def __init__(self):
        super().__init__()
        self._auth = GerenciadorAuth()
        self._configurar_janela()
        self._construir_interface()

    # ── Configuração ──────────────────────────────────────────────────────
    def _configurar_janela(self):
        self.setWindowTitle("J.A.R.V.I.S — Autenticação")
        self.setFixedSize(560, 620)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

    # ── Interface ─────────────────────────────────────────────────────────
    def _construir_interface(self):
        # Camada de fundo animada
        self._fundo = FundoAnimado(self)
        self._fundo.setGeometry(0, 0, self.width(), self.height())
        self._fundo.lower()

        # Container central
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)

        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QWidget#container {{
                background: rgba(3, 8, 16, 238);
                border: 1px solid rgba(0, 100, 180, 120);
                border-radius: 14px;
            }}
        """)
        layout_raiz.addWidget(container)

        vl = QVBoxLayout(container)
        vl.setContentsMargins(50, 40, 50, 40)
        vl.setSpacing(16)

        # ── Cabeçalho ─────────────────────────────────────────────────────
        icone = QLabel("⬡")
        icone.setAlignment(Qt.AlignCenter)
        icone.setStyleSheet(f"""
            color: {CIANO};
            font-size: 36px;
            background: transparent;
            margin-bottom: 2px;
        """)
        vl.addWidget(icone)

        titulo = QLabel("J.A.R.V.I.S")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(f"""
            color: {CIANO};
            font-family: 'Orbitron', 'Consolas', monospace;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 10px;
            background: transparent;
        """)
        vl.addWidget(titulo)

        sub = QLabel("SISTEMA DE CONTROLE AVANÇADO")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"""
            color: rgba(0, 100, 160, 200);
            font-family: 'Consolas', monospace;
            font-size: 9px;
            letter-spacing: 4px;
            background: transparent;
            margin-bottom: 10px;
        """)
        vl.addWidget(sub)

        # Separador
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: rgba(0, 80, 140, 100); border: none; max-height: 1px;")
        vl.addWidget(sep)
        vl.addSpacing(10)

        # ── Rótulo "AUTENTICAÇÃO BIOMÉTRICA" ─────────────────────────────
        auth_label = QLabel("▸ AUTENTICAÇÃO DE ACESSO")
        auth_label.setAlignment(Qt.AlignCenter)
        auth_label.setStyleSheet(f"""
            color: rgba(0, 140, 200, 180);
            font-family: 'Consolas', monospace;
            font-size: 10px;
            letter-spacing: 3px;
            background: transparent;
            margin-bottom: 6px;
        """)
        vl.addWidget(auth_label)

        # ── Campo: Usuário ─────────────────────────────────────────────────
        lbl_usuario = QLabel("IDENTIFICAÇÃO DE USUÁRIO")
        lbl_usuario.setStyleSheet(self._estilo_label())
        vl.addWidget(lbl_usuario)

        self._campo_usuario = QLineEdit()
        self._campo_usuario.setPlaceholderText("Digite seu usuário...")
        self._campo_usuario.setFixedHeight(44)
        self._campo_usuario.setStyleSheet(ESTILO_CAMPO)
        self._campo_usuario.returnPressed.connect(lambda: self._campo_senha.setFocus())
        vl.addWidget(self._campo_usuario)

        # ── Campo: Senha ───────────────────────────────────────────────────
        lbl_senha = QLabel("CÓDIGO DE ACESSO")
        lbl_senha.setStyleSheet(self._estilo_label())
        vl.addWidget(lbl_senha)

        self._campo_senha = QLineEdit()
        self._campo_senha.setPlaceholderText("Digite sua senha...")
        self._campo_senha.setEchoMode(QLineEdit.Password)
        self._campo_senha.setFixedHeight(44)
        self._campo_senha.setStyleSheet(ESTILO_CAMPO)
        self._campo_senha.returnPressed.connect(self._tentar_login)
        vl.addWidget(self._campo_senha)

        vl.addSpacing(6)

        # ── Mensagem de feedback ───────────────────────────────────────────
        self._lbl_feedback = QLabel("")
        self._lbl_feedback.setAlignment(Qt.AlignCenter)
        self._lbl_feedback.setFixedHeight(22)
        self._lbl_feedback.setStyleSheet(f"""
            color: transparent;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            letter-spacing: 2px;
            background: transparent;
        """)
        vl.addWidget(self._lbl_feedback)

        # ── Botão de login ─────────────────────────────────────────────────
        self._btn_login = BotaoFuturista("  ▶  INICIAR ACESSO  ▶", AZUL_NEON)
        self._btn_login.clicked.connect(self._tentar_login)
        vl.addWidget(self._btn_login)

        vl.addSpacing(4)

        # ── Linha de dica ──────────────────────────────────────────────────
        dica = QLabel(f"Padrão: {USUARIO_PADRAO}  /  {SENHA_PADRAO}")
        dica.setAlignment(Qt.AlignCenter)
        dica.setStyleSheet(f"""
            color: rgba(0, 60, 100, 160);
            font-family: 'Consolas', monospace;
            font-size: 9px;
            letter-spacing: 1px;
            background: transparent;
        """)
        vl.addWidget(dica)

        vl.addSpacing(4)

        # Separador inferior
        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: rgba(0, 60, 120, 80); border: none; max-height: 1px;")
        vl.addWidget(sep2)

        # ── Rodapé ─────────────────────────────────────────────────────────
        rodape = QLabel("SEGURANÇA NÍVEL 5  ·  CRIPTOGRAFIA SHA-256  ·  J.A.R.V.I.S v8.1")
        rodape.setAlignment(Qt.AlignCenter)
        rodape.setStyleSheet(f"""
            color: rgba(0, 60, 100, 140);
            font-family: 'Consolas', monospace;
            font-size: 8px;
            letter-spacing: 2px;
            background: transparent;
            margin-top: 4px;
        """)
        vl.addWidget(rodape)

        # Foco inicial
        self._campo_usuario.setFocus()

    def _estilo_label(self) -> str:
        return f"""
            color: rgba(0, 130, 200, 200);
            font-family: 'Consolas', monospace;
            font-size: 9px;
            letter-spacing: 3px;
            font-weight: 700;
            background: transparent;
            margin-bottom: 2px;
        """

    # ── Lógica de login ───────────────────────────────────────────────────
    def _tentar_login(self):
        usuario = self._campo_usuario.text().strip()
        senha   = self._campo_senha.text()

        if not usuario or not senha:
            self._mostrar_feedback("PREENCHA TODOS OS CAMPOS", AZUL_NEON)
            return

        if self._auth.verificar_login(usuario, senha):
            self._auth.salvar_sessao(usuario)
            self._mostrar_feedback(f"✓  ACESSO CONCEDIDO  —  BEM-VINDO, {usuario.upper()}", VERDE_OK)
            # Aguarda feedback e emite sinal
            QTimer.singleShot(1200, lambda: self._on_login_ok(usuario))
        else:
            self._mostrar_feedback("✗  ACESSO NEGADO  —  CREDENCIAIS INVÁLIDAS", VERMELHO)
            # Limpa a senha e coloca foco nela
            self._campo_senha.clear()
            QTimer.singleShot(600, lambda: self._campo_senha.setFocus())

    def _on_login_ok(self, usuario: str):
        self.close()
        self.login_aprovado.emit(usuario)

    def _mostrar_feedback(self, texto: str, cor: str):
        self._lbl_feedback.setText(texto)
        self._lbl_feedback.setStyleSheet(f"""
            color: {cor};
            font-family: 'Consolas', monospace;
            font-size: 11px;
            letter-spacing: 2px;
            background: transparent;
        """)
        # Limpa automaticamente após N segundos
        QTimer.singleShot(TEMPO_FEEDBACK_MS, self._limpar_feedback)

    def _limpar_feedback(self):
        self._lbl_feedback.setText("")
        self._lbl_feedback.setStyleSheet("color: transparent; background: transparent;")

    # ── Arrastar janela ───────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    # ── API: verificar sessão já ativa ────────────────────────────────────
    def sessao_existente(self) -> str | None:
        """Retorna usuário logado se a sessão estiver ativa, senão None."""
        return self._auth.sessao_ativa()


# ═══════════════════════════════════════════════════════════════════════════════
# TESTE ISOLADO
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginScreen()
    login.login_aprovado.connect(lambda u: print(f"Login aprovado: {u}"))
    login.show()
    sys.exit(app.exec())
