"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              J.A.R.V.I.S  —  LAUNCHER PRINCIPAL  v1.1                     ║
║         Orquestra: Boot  →  Login  →  Sistema Principal                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  COMO USAR:                                                                  ║
║  1. Coloque este arquivo NA MESMA PASTA que o seu sistema principal          ║
║     (o arquivo que contém a classe JarvisUI)                                ║
║  2. Ajuste a variável ARQUIVO_SISTEMA_PRINCIPAL abaixo                      ║
║  3. Execute: python jarvis_launcher.py                                       ║
║                                                                              ║
║  FLUXO:                                                                      ║
║    jarvis_launcher.py  →  jarvis_boot.py  →  jarvis_login.py                ║
║                        →  [sistema principal] (sem modificações)             ║
╚══════════════════════════════════════════════════════════════════════════════╝

ESTRUTURA DE ARQUIVOS ESPERADA:
  📁 pasta_do_projeto/
  ├── jarvis_launcher.py          ← ESTE arquivo (ponto de entrada)
  ├── jarvis_boot.py              ← Tela de boot (Reator ARC)
  ├── jarvis_login.py             ← Tela de login
  ├── jarvis_auth.json            ← Criado automaticamente no 1º login
  └── seu_sistema_principal.py   ← Seu código existente (NÃO modificado)
"""

import sys
import os
import threading
import tempfile
import hashlib
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui     import QColor, QPalette
from PySide6.QtCore    import Qt, QTimer

# Importa as telas criadas
from jarvis_boot  import BootScreen
from jarvis_login import LoginScreen

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️  CONFIGURAÇÃO  ——  AJUSTE AQUI O NOME DO SEU ARQUIVO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
#
# Coloque o nome do módulo Python do seu sistema (sem .py)
# Exemplo: se o arquivo é "meu_jarvis.py" → coloque "meu_jarvis"
#
MODULO_SISTEMA_PRINCIPAL = "JarvisMark51"   # ← ALTERE PARA O NOME DO SEU ARQUIVO
#
# Nome da classe principal da interface no módulo acima:
CLASSE_UI_PRINCIPAL = "JarvisUI"         # ← ALTERE SE A CLASSE TIVER OUTRO NOME
#
# ─────────────────────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════════════════════
# VOICE ENGINE LEVE (para o launcher — independente do sistema principal)
# ═══════════════════════════════════════════════════════════════════════════════
_ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY",
                        "sk_84233d7a9ad0297a214f7a202f5f8b35a27d8c53a6caf760")
_ELEVENLABS_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"   # Daniel
_ELEVENLABS_MODEL    = "eleven_multilingual_v2"

_eleven_client = None
_VOICE_OK = False
_PG_OK    = False

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    _PG_OK = True
except Exception:
    pass

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    _eleven_client = ElevenLabs(api_key=_ELEVENLABS_API_KEY)
    _VOICE_OK = True
except Exception:
    pass

_CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_eleven_cache"
_CACHE_DIR.mkdir(exist_ok=True)


def _launcher_speak(text: str):
    """Fala o texto usando ElevenLabs + pygame. Roda na thread que chama."""
    if not _VOICE_OK or not _PG_OK or _eleven_client is None:
        print(f"[Launcher Voice] (sem áudio) {text}")
        return
    try:
        # Verificar cache
        key = f"{_ELEVENLABS_VOICE_ID}:{_ELEVENLABS_MODEL}:{text}"
        h = hashlib.md5(key.encode()).hexdigest()
        cache_path = _CACHE_DIR / f"{h}.mp3"

        if not cache_path.exists() or cache_path.stat().st_size == 0:
            audio = _eleven_client.text_to_speech.convert(
                voice_id=_ELEVENLABS_VOICE_ID,
                text=text,
                model_id=_ELEVENLABS_MODEL,
                voice_settings=VoiceSettings(
                    stability=0.55,
                    similarity_boost=0.80,
                    style=0.20,
                    use_speaker_boost=True,
                ),
            )
            data = b"".join(audio)
            cache_path.write_bytes(data)

        pygame.mixer.music.load(str(cache_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except Exception as e:
        print(f"[Launcher Voice] Erro: {e}")


def _speak_async(text: str):
    """Dispara a fala em uma thread separada para não travar a UI."""
    threading.Thread(target=_launcher_speak, args=(text,), daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# PALETA GLOBAL (mantém o estilo escuro do sistema principal)
# ═══════════════════════════════════════════════════════════════════════════════
def aplicar_paleta(app: QApplication):
    """Aplica a paleta escura do sistema JARVIS ao QApplication."""
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor("#030810"))
    pal.setColor(QPalette.WindowText,      QColor("#D0E8FF"))
    pal.setColor(QPalette.Base,            QColor("#060D1A"))
    pal.setColor(QPalette.AlternateBase,   QColor("#0A1424"))
    pal.setColor(QPalette.Text,            QColor("#D0E8FF"))
    pal.setColor(QPalette.Button,          QColor("#060D1A"))
    pal.setColor(QPalette.ButtonText,      QColor("#D0E8FF"))
    pal.setColor(QPalette.Highlight,       QColor("#0A2040"))
    pal.setColor(QPalette.HighlightedText, QColor("#4DB8FF"))
    pal.setColor(QPalette.Link,            QColor("#1A8FFF"))
    pal.setColor(QPalette.ToolTipBase,     QColor("#0A1424"))
    pal.setColor(QPalette.ToolTipText,     QColor("#D0E8FF"))
    app.setPalette(pal)


# ═══════════════════════════════════════════════════════════════════════════════
# ORQUESTRADOR DO FLUXO
# ═══════════════════════════════════════════════════════════════════════════════
class Launcher:
    """
    Controla a sequência de inicialização:
      1. Boot (animação do Reator ARC)
      2. Login (ou pula se já logado)
      3. Sistema principal
    """

    def __init__(self, app: QApplication):
        self._app        = app
        self._boot       = None
        self._login      = None
        self._sistema    = None

    # ── Ponto de entrada ──────────────────────────────────────────────────
    def iniciar(self):
        _speak_async("Inicializando sistemas jarvis Aguarde, senhor.")
        self._mostrar_boot()

    # ── Etapa 1: Boot ─────────────────────────────────────────────────────
    def _mostrar_boot(self):
        print("[Launcher] Iniciando tela de boot...")
        self._boot = BootScreen()
        self._boot.boot_concluido.connect(self._apos_boot)
        self._boot.show()

    # ── Etapa 2: Login (ou pula) ──────────────────────────────────────────
    def _apos_boot(self):
        print("[Launcher] Boot concluído. Verificando sessão...")
        _speak_async("Sequência de boot concluída. Verificando credenciais.")
        self._login = LoginScreen()

        # Verifica se já existe sessão ativa salva
        usuario_logado = self._login.sessao_existente()
        if usuario_logado:
            print(f"[Launcher] Sessão ativa encontrada: {usuario_logado} — pulando login.")
            _speak_async(f"Bem-vindo de volta, {usuario_logado}. Carregando interface principal.")
            QTimer.singleShot(0, lambda: self._iniciar_sistema(usuario_logado))
        else:
            print("[Launcher] Nenhuma sessão ativa. Exibindo tela de login.")
            _speak_async("Nenhuma sessão ativa encontrada. Por favor, autentique-se.")
            self._login.login_aprovado.connect(self._iniciar_sistema)
            self._login.show()

    # ── Etapa 3: Sistema principal ────────────────────────────────────────
    def _iniciar_sistema(self, usuario: str):
        print(f"[Launcher] Acesso concedido para '{usuario}'. Carregando sistema principal...")
        try:
            # Importa dinamicamente o módulo do sistema principal
            import importlib
            modulo = importlib.import_module(MODULO_SISTEMA_PRINCIPAL)
            ClasseUI = getattr(modulo, CLASSE_UI_PRINCIPAL)

            # Instancia e exibe a interface principal
            self._sistema = ClasseUI()
            self._sistema.run()
            self._app.setQuitOnLastWindowClosed(True)

        except ImportError as e:
            print(f"\n[Launcher] ❌ ERRO: Módulo '{MODULO_SISTEMA_PRINCIPAL}' não encontrado.")
            print(f"   Detalhe: {e}")
            print(f"\n   ➤ Verifique a variável MODULO_SISTEMA_PRINCIPAL em jarvis_launcher.py")
            print(f"   ➤ Arquivo esperado: {MODULO_SISTEMA_PRINCIPAL}.py na mesma pasta\n")
            _speak_async("Erro crítico. Módulo principal não encontrado.")
            self._app.quit()

        except AttributeError as e:
            print(f"\n[Launcher] ❌ ERRO: Classe '{CLASSE_UI_PRINCIPAL}' não encontrada em '{MODULO_SISTEMA_PRINCIPAL}'.")
            print(f"   Detalhe: {e}")
            print(f"\n   ➤ Verifique a variável CLASSE_UI_PRINCIPAL em jarvis_launcher.py\n")
            _speak_async("Erro crítico. Classe da interface não encontrada.")
            self._app.quit()

        except Exception as e:
            print(f"\n[Launcher] ❌ ERRO inesperado ao iniciar o sistema: {e}\n")
            import traceback
            traceback.print_exc()
            _speak_async("Erro inesperado durante a inicialização do sistema.")
            self._app.quit()


# ═══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Garante que o diretório do script está no PATH (para importar módulos irmãos)
    script_dir = str(Path(__file__).parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)  # Evita fechamento na transição das telas
    aplicar_paleta(app)

    launcher = Launcher(app)
    launcher.iniciar()

    sys.exit(app.exec())
