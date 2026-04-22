"""
╔══════════════════════════════════════════════════════════════════════╗
║        J.A.R.V.I.S  —  GESTURE MASTER HUD v5.1                     ║
║  VOZ JARVIS DO FILME  +  Comandos de voz completos                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  INSTALAÇÃO COMPLETA:                                                ║
║    pip install mediapipe opencv-python numpy pyautogui               ║
║    pip install SpeechRecognition psutil pywin32 pycaw comtypes       ║
║    pip install edge-tts pygame                                       ║
║    (edge-tts requer conexão com internet para gerar a voz)           ║
╠══════════════════════════════════════════════════════════════════════╣
║  VOZ:                                                                ║
║    • Motor: Microsoft Edge TTS Neural (GRÁTIS, sem API key)          ║
║    • Voz: en-GB-RyanNeural  — britânico, grave, formal               ║
║    • Pitch: -8Hz  Rate: -5%  → soa como o JARVIS do filme            ║
║    • Cache: respostas comuns pré-geradas para resposta INSTANTÂNEA   ║
║    • Fala inglês como JARVIS, entende comandos em PT-BR              ║
╠══════════════════════════════════════════════════════════════════════╣
║  WAKE WORD: fale "JARVIS" → responde "Yes, sir." imediatamente       ║
║  COMANDOS PT-BR: após ativar, diga qualquer comando                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk
import threading, datetime, os, random, time, subprocess
import platform, socket, ctypes, queue, math, asyncio
import tempfile, hashlib, json
from pathlib import Path

# ── Imports opcionais ───────────────────────────────────────
try:
    import cv2, mediapipe as mp, numpy as np
    CV2_OK = True
except: CV2_OK = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
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
# MOTOR DE VOZ  —  JARVIS  (edge-tts  en-GB-RyanNeural)
# ═══════════════════════════════════════════════════════════

# Diretório de cache de áudio
CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_voice_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Configuração da voz JARVIS
JARVIS_VOICE  = "en-GB-RyanNeural"   # voz britânica masculina — mais próxima de JARVIS
JARVIS_RATE   = "-5%"                # ligeiramente mais lento = mais solene
JARVIS_PITCH  = "-8Hz"              # mais grave = mais autoritário

# Respostas pré-cacheadas (geradas uma vez e reutilizadas instantaneamente)
PRECACHE_PHRASES = [
    "Yes, sir.",
    "Of course, sir.",
    "Certainly, sir.",
    "Right away, sir.",
    "All systems are operational, sir.",
    "As you wish, sir.",
    "I understand, sir.",
    "Camera activated. Gesture control is now online, sir.",
    "Camera deactivated, sir.",
    "Gesture control ready. All modules loaded, sir.",
    "Switching to cursor mode, sir.",
    "Switching to hotkey mode, sir.",
    "Switching to volume mode, sir.",
    "Switching to JARVIS mode, sir.",
    "Opening Google, sir.",
    "Opening YouTube, sir.",
    "Opening Spotify, sir.",
    "Opening Discord, sir.",
    "Opening GitHub, sir.",
    "Opening WhatsApp, sir.",
    "Opening Netflix, sir.",
    "Volume increased, sir.",
    "Volume decreased, sir.",
    "Audio muted, sir.",
    "Screenshot captured and saved, sir.",
    "Locking the workstation, sir.",
    "Shutting down in five seconds, sir.",
    "Restarting the system, sir.",
    "Menu reset, sir.",
    "Drag initiated, sir.",
    "Drag released, sir.",
    "Left click confirmed, sir.",
    "Double click confirmed, sir.",
    "Right click confirmed, sir.",
    "JARVIS Gesture Master online. All modules loaded. Ready for your command, sir.",
]

_voz_q   = queue.Queue()
_speak_ready = threading.Event()

def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def _cache_path(text: str) -> Path:
    return CACHE_DIR / f"{_cache_key(text)}.mp3"

async def _generate_audio(text: str, path: Path):
    """Gera áudio com edge-tts e salva em arquivo."""
    communicate = edge_tts.Communicate(
        text,
        JARVIS_VOICE,
        rate=JARVIS_RATE,
        pitch=JARVIS_PITCH,
    )
    await communicate.save(str(path))

def _ensure_cached(text: str) -> Path:
    """Garante que o áudio está em cache. Gera se necessário."""
    path = _cache_path(text)
    if not path.exists():
        try:
            asyncio.run(_generate_audio(text, path))
        except Exception as e:
            return None
    return path

def _precache_worker():
    """Thread de background que pré-gera todas as frases comuns."""
    for phrase in PRECACHE_PHRASES:
        _ensure_cached(phrase)
    _speak_ready.set()

def _play_audio(path: Path):
    """Reproduz um arquivo MP3 com pygame."""
    if not PG_OK or not path or not path.exists():
        return
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except Exception:
        pass

def _voz_worker():
    """Worker thread que processa a fila de falas."""
    while True:
        text = _voz_q.get()
        try:
            if EDGE_OK and PG_OK:
                path = _ensure_cached(text)
                if path:
                    _play_audio(path)
                else:
                    # fallback para pyttsx3 se edge-tts falhar
                    _pyttsx3_fallback(text)
            else:
                _pyttsx3_fallback(text)
        except Exception:
            pass
        _voz_q.task_done()

def _pyttsx3_fallback(text: str):
    """Fallback: usa pyttsx3 se edge-tts não disponível."""
    try:
        import pyttsx3
        e = pyttsx3.init()
        e.setProperty('rate', 160)
        for v in e.getProperty('voices'):
            if 'english' in v.name.lower():
                e.setProperty('voice', v.id); break
        e.say(text); e.runAndWait()
    except: pass

# Inicia o worker de voz
threading.Thread(target=_voz_worker, daemon=True).start()
# Pré-cacheia frases em background
threading.Thread(target=_precache_worker, daemon=True).start()

def speak(text: str, ui=None):
    """Enfileira texto para ser falado por JARVIS."""
    if ui:
        ui.add_log(f"JARVIS › {text}", "jarvis")
    _voz_q.put(text)

# Mapa PT-BR → inglês JARVIS para respostas de wake word / confirmações
PTBR_TO_EN = {
    # wake word
    "jarvis": "Yes, sir.",
    # confirmações gerais
    "sim": "Of course, sir.",
    "ok": "Right away, sir.",
    "obrigado": "My pleasure, sir.",
    # apps
    "abre o google": "Opening Google, sir.",
    "google": "Opening Google, sir.",
    "youtube": "Opening YouTube, sir.",
    "spotify": "Opening Spotify, sir.",
    "discord": "Opening Discord, sir.",
    "whatsapp": "Opening WhatsApp, sir.",
    "netflix": "Opening Netflix, sir.",
    "github": "Opening GitHub, sir.",
    "chatgpt": "Opening ChatGPT, sir.",
    "gmail": "Opening Gmail, sir.",
    # sistema
    "status": "Fetching system diagnostics, sir.",
    "hora": None,          # fala dinâmica
    "data": None,          # fala dinâmica
    "screenshot": "Screenshot captured and saved to your Pictures folder, sir.",
    "bloqueia": "Locking the workstation, sir.",
    "desliga": "Initiating shutdown sequence in five seconds, sir.",
    "reinicia": "Restarting the system, sir.",
    # volume
    "volume": None,        # fala dinâmica
    # modos
    "modo cursor": "Switching to cursor mode, sir.",
    "modo hotkey": "Switching to hotkey mode, sir.",
    "modo volume": "Switching to volume mode, sir.",
    "modo jarvis": "Switching to JARVIS mode, sir.",
    # sair
    "sair": "Shutting down JARVIS. Good day, sir.",
    "fechar jarvis": "Shutting down JARVIS. Good day, sir.",
}

def jarvis_response(query_ptbr: str) -> str:
    """Retorna a resposta JARVIS em inglês para um dado comando."""
    q = query_ptbr.lower().strip()
    for key, resp in PTBR_TO_EN.items():
        if key in q and resp:
            return resp
    # fallback respostas genéricas em inglês estilo JARVIS
    fallbacks = [
        "Understood, sir.",
        "Processing your request, sir.",
        "Command acknowledged, sir.",
        "Noted, sir.",
        "I'm on it, sir.",
        "Affirmative, sir.",
        "Consider it done, sir.",
    ]
    return random.choice(fallbacks)

# ═══════════════════════════════════════════════════════════
# SISTEMA
# ═══════════════════════════════════════════════════════════
def sys_info():
    try:
        cpu  = psutil.cpu_percent(interval=0.2) if PS_OK else 0
        ram  = psutil.virtual_memory()           if PS_OK else None
        disk = psutil.disk_usage('/')            if PS_OK else None
        bat  = psutil.sensors_battery()          if PS_OK else None
        host = socket.gethostname()
        ip   = socket.gethostbyname(host)
        return dict(
            cpu  = f"{cpu:.0f}%",
            ram  = f"{ram.percent:.0f}%" if ram  else "N/A",
            disk = f"{disk.percent:.0f}%" if disk else "N/A",
            bat  = (f"{bat.percent:.0f}%{'⚡' if bat.power_plugged else '🔋'}") if bat else "N/A",
            ip   = ip, host=host,
            os   = f"{platform.system()} {platform.release()}",
        )
    except: return {k:"?" for k in ["cpu","ram","disk","bat","ip","host","os"]}

def vol_ctrl(d):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        dev   = AudioUtilities.GetSpeakers()
        iface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol   = cast(iface, POINTER(IAudioEndpointVolume))
        if d=='up':   vol.SetMasterVolumeLevel(min(vol.GetMasterVolumeLevel()+2., 0.),None)
        elif d=='dn': vol.SetMasterVolumeLevel(max(vol.GetMasterVolumeLevel()-2.,-65.25),None)
        elif d=='mu': vol.SetMute(not vol.GetMute(),None)
    except:
        if AG_OK:
            {'up':lambda:pyautogui.press('volumeup'),
             'dn':lambda:pyautogui.press('volumedown'),
             'mu':lambda:pyautogui.press('volumemute')}.get(d,lambda:None)()

# ═══════════════════════════════════════════════════════════
# MOTOR DE GESTOS
# ═══════════════════════════════════════════════════════════
class GestureEngine:
    TIPS = [4,8,12,16,20]

    def __init__(self):
        self.ok = CV2_OK
        if not self.ok: return
        self.mh    = mp.solutions.hands
        self.hands = self.mh.Hands(
            static_image_mode=False, max_num_hands=2,
            min_detection_confidence=0.75, min_tracking_confidence=0.70)
        self.draw  = mp.solutions.drawing_utils
        self.cap   = None
        self._buf  = {}
        self.HOLD  = 8

    def _fingers(self, lm):
        f = [1 if lm[4].x < lm[3].x else 0]
        for t in self.TIPS[1:]:
            f.append(1 if lm[t].y < lm[t-2].y else 0)
        return f

    def _fist(self, lm):
        return sum(1 for t in self.TIPS[1:] if lm[t].y > lm[t-2].y) >= 4

    def _pinch_dist(self, lm):
        return math.hypot(lm[4].x-lm[8].x, lm[4].y-lm[8].y)

    def _classify(self, lm):
        ff    = self._fingers(lm)
        n     = sum(ff)
        fist  = self._fist(lm)
        pinch = self._pinch_dist(lm)
        is_open = (n == 5)
        ix,iy = lm[8].x, lm[8].y
        mx,my = lm[12].x,lm[12].y
        wx,wy = lm[0].x, lm[0].y
        if fist:             g = "PUNHO"
        elif pinch < 0.042:  g = "PINCA"
        elif is_open:        g = "PALMA"
        elif n==1 and ff[1]: g = "1_DEDO"
        elif n==2 and ff[1] and ff[2]: g = "2_DEDOS"
        elif n==3 and ff[1] and ff[2] and ff[3]: g = "3_DEDOS"
        elif n==4: g = "4_DEDOS"
        else:      g = f"{n}_GEN"
        return dict(g=g,n=n,ff=ff,fist=fist,pinch=pinch,is_open=is_open,
                    ix=ix,iy=iy,mx=mx,my=my,wx=wx,wy=wy,lm=lm)

    def _confirm(self, hand_id, g_name):
        key = (hand_id, g_name)
        for k in list(self._buf):
            if k[0]==hand_id and k!=key: self._buf[k]=0
        self._buf[key] = self._buf.get(key,0)+1
        return self._buf[key]==self.HOLD

    def start(self):
        if not self.ok: return False
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def stop(self):
        if self.cap: self.cap.release()

    def read(self):
        if not self.ok or not self.cap: return None,None,None,None,None
        ret,frame = self.cap.read()
        if not ret: return None,None,None,None,None
        frame = cv2.flip(frame,1)
        rgb   = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        res   = self.hands.process(rgb)
        h,w   = frame.shape[:2]
        right=left=conf_r=conf_l=None
        if res.multi_hand_landmarks and res.multi_handedness:
            for hlm,hness in zip(res.multi_hand_landmarks,res.multi_handedness):
                label = hness.classification[0].label
                lm    = hlm.landmark
                data  = self._classify(lm)
                hid   = 0 if label=='Right' else 1
                col   = (0,220,255) if label=='Right' else (255,160,0)
                self.draw.draw_landmarks(frame,hlm,self.mh.HAND_CONNECTIONS,
                    self.draw.DrawingSpec(color=col,thickness=2,circle_radius=3),
                    self.draw.DrawingSpec(color=(40,40,180),thickness=2))
                gx,gy = int(lm[0].x*w),int(lm[0].y*h)
                cv2.putText(frame,data['g'],(gx-30,gy+20),
                            cv2.FONT_HERSHEY_SIMPLEX,0.5,col,2)
                confirmed = self._confirm(hid,data['g'])
                if label=='Right':
                    right=data
                    if confirmed: conf_r=data
                else:
                    left=data
                    if confirmed: conf_l=data
        cv2.rectangle(frame,(0,0),(w,32),(5,13,26),-1)
        r_txt=right['g'] if right else "—"
        l_txt=left['g']  if left  else "—"
        cv2.putText(frame,f"DIR:{r_txt}  ESQ:{l_txt}",(6,22),
                    cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,220,255),2)
        return frame,right,left,conf_r,conf_l


# ═══════════════════════════════════════════════════════════
# GESTURE CONTROLLER
# ═══════════════════════════════════════════════════════════
class GestureController:
    MODES = ["CURSOR","HOTKEY","VOLUME","JARVIS"]

    def __init__(self, ui):
        self.ui   = ui
        self.mode = "CURSOR"
        self._sw,self._sh = (pyautogui.size() if AG_OK else (1920,1080))
        self._dragging   = False
        self._scroll_ref = None
        self._smooth     = None
        self._SMTH       = 0.30
        self._last_pinch = 0.0
        self._open_hold  = 0
        self.OPEN_THRESH = 14

    def set_mode(self, m):
        if m in self.MODES:
            self.mode = m
            self.ui.add_log(f"◈ MODO → {m}", "gesto")
            mode_voices = {
                "CURSOR": "Switching to cursor mode, sir.",
                "HOTKEY": "Switching to hotkey mode, sir.",
                "VOLUME": "Switching to volume mode, sir.",
                "JARVIS": "Switching to JARVIS mode, sir.",
            }
            speak(mode_voices.get(m,"Mode changed, sir."), self.ui)
            self.ui.root.after(0, lambda: self.ui.highlight_mode(m))

    def _scr(self,nx,ny):
        M=0.12
        return int(max(0.,min(1.,(nx-M)/(1-2*M)))*self._sw), \
               int(max(0.,min(1.,(ny-M)/(1-2*M)))*self._sh)

    def _mv(self,nx,ny):
        tx,ty=self._scr(nx,ny)
        if self._smooth is None: self._smooth=(tx,ty)
        cx,cy=self._smooth
        S=self._SMTH
        nx2=max(0,min(self._sw-1,int(cx+(tx-cx)*S*2)))
        ny2=max(0,min(self._sh-1,int(cy+(ty-cy)*S*2)))
        self._smooth=(nx2,ny2)
        return nx2,ny2

    def _cursor(self,right,left,cr,cl):
        if not AG_OK or right is None: return
        g=right['g']
        if g=="1_DEDO":
            x,y=self._mv(right['ix'],right['iy'])
            pyautogui.moveTo(x,y,_pause=False)
            if self._dragging:
                pyautogui.mouseUp(button='left',_pause=False)
                self._dragging=False
            self._scroll_ref=None; self._open_hold=0
        elif g=="2_DEDOS":
            my=right['my']
            if self._scroll_ref is None: self._scroll_ref=my
            else:
                dy=(self._scroll_ref-my)*25
                if abs(dy)>0.25:
                    pyautogui.scroll(int(dy),_pause=False)
                    self._scroll_ref=my
        elif g=="PUNHO":
            x,y=self._mv(right['wx'],right['wy'])
            if not self._dragging:
                pyautogui.mouseDown(button='left',_pause=False)
                self._dragging=True
                self.ui.add_log("✊ ARRASTAR — iniciado","gesto")
                speak("Drag initiated, sir.",self.ui)
            pyautogui.moveTo(x,y,_pause=False)
            self._scroll_ref=None
        elif g=="PALMA":
            self._open_hold+=1
            if self._open_hold==self.OPEN_THRESH:
                pyautogui.rightClick(_pause=False)
                self.ui.add_log("✋ CLIQUE DIREITO","gesto")
                speak("Right click confirmed, sir.",self.ui)
        else:
            self._open_hold=0
        if g!="PUNHO" and self._dragging:
            pyautogui.mouseUp(button='left',_pause=False)
            self._dragging=False
            self.ui.add_log("✊ ARRASTAR — solto","gesto")
            speak("Drag released, sir.",self.ui)
        if cr and cr['g']=="PINCA":
            now=time.time()
            if now-self._last_pinch<0.40:
                pyautogui.doubleClick(_pause=False)
                self.ui.add_log("🤌 DUPLO CLIQUE","gesto")
                speak("Double click confirmed, sir.",self.ui)
            else:
                pyautogui.click(_pause=False)
                self.ui.add_log("🤌 CLIQUE","gesto")
                speak("Left click confirmed, sir.",self.ui)
            self._last_pinch=now

    def _hotkey(self,right,left,cr,cl):
        if not AG_OK or cr is None: return
        g=cr['g']
        actions={
            "1_DEDO":  (('alt','tab'),  "Switching windows, sir."),
            "2_DEDOS": (('win','d'),    "Showing the desktop, sir."),
            "3_DEDOS": (('win','tab'),  "Opening task view, sir."),
            "PALMA":   (('win','left'), "Snapping window to the left, sir."),
            "PUNHO":   (('alt','f4'),   "Closing the active window, sir."),
        }
        if g=="4_DEDOS":
            try:
                p=os.path.join(Path.home(),"Pictures",
                    f"jarvis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                pyautogui.screenshot(p)
                self.ui.add_log(f"📸 Screenshot → {p}","gesto")
                speak("Screenshot captured and saved, sir.",self.ui)
            except Exception as e:
                self.ui.add_log(f"⚠ {e}","erro")
        elif g in actions:
            keys,msg=actions[g]
            pyautogui.hotkey(*keys,_pause=False)
            self.ui.add_log(f"⌨ {g}","gesto")
            speak(msg,self.ui)

    def _volume(self,right,left,cr,cl):
        if right and left:
            dist=math.hypot(right['ix']-left['ix'],right['iy']-left['iy'])
            pct=int(max(0.,min(1.,(dist-0.05)/0.70))*100)
            self.ui.root.after(0,lambda p=pct:self.ui.vol_var.set(p))
        if cr:
            if cr['g']=="1_DEDO":  vol_ctrl('up'); self.ui.add_log("🔊 Volume +","gesto"); speak("Volume increased, sir.",self.ui)
            elif cr['g']=="PUNHO": vol_ctrl('mu'); self.ui.add_log("🔇 Mute","gesto");    speak("Audio muted, sir.",self.ui)
        if right and right['g']=="2_DEDOS": vol_ctrl('dn'); self.ui.add_log("🔉 Volume -","gesto")

    def _jarvis(self,right,left,cr,cl):
        if cr is None: return
        g=cr['g']
        if   g=="1_DEDO":  self.ui.root.after(0,self.ui.menu_up)
        elif g=="2_DEDOS": self.ui.root.after(0,self.ui.menu_down)
        elif g=="3_DEDOS": self.ui.root.after(0,self.ui.menu_confirm)
        elif g=="PALMA":
            self.ui.menu_idx=0
            self.ui.root.after(0,self.ui.refresh_menu)
            speak("Menu reset, sir.",self.ui)
        elif g=="PUNHO":
            for _ in range(3): self.ui.root.after(0,self.ui.menu_down)

    def process(self,right,left,cr,cl):
        if cl:
            g=cl['g']
            m={"1_DEDO":"CURSOR","2_DEDOS":"HOTKEY","3_DEDOS":"VOLUME","PALMA":"JARVIS"}.get(g)
            if m: self.set_mode(m)
        if   self.mode=="CURSOR": self._cursor(right,left,cr,cl)
        elif self.mode=="HOTKEY": self._hotkey(right,left,cr,cl)
        elif self.mode=="VOLUME": self._volume(right,left,cr,cl)
        elif self.mode=="JARVIS": self._jarvis(right,left,cr,cl)


# ═══════════════════════════════════════════════════════════
# HANDLER DE COMANDOS
# ═══════════════════════════════════════════════════════════
SITES = {
    "youtube":  ("https://youtube.com",          "YouTube"),
    "google":   ("https://google.com",           "Google"),
    "github":   ("https://github.com",           "GitHub"),
    "chatgpt":  ("https://chat.openai.com",      "ChatGPT"),
    "gmail":    ("https://mail.google.com",       "Gmail"),
    "whatsapp": ("https://web.whatsapp.com",      "WhatsApp"),
    "netflix":  ("https://netflix.com",           "Netflix"),
    "twitch":   ("https://twitch.tv",             "Twitch"),
    "reddit":   ("https://reddit.com",            "Reddit"),
    "linkedin": ("https://linkedin.com",          "LinkedIn"),
}

def cmd(query, ui):
    q = query.lower().strip()
    if not q: return

    # ── HORA / DATA ──────────────────────────────────────
    if "hora" in q or "que horas" in q:
        agora = datetime.datetime.now().strftime('%H:%M')
        speak(f"The current time is {agora}, sir.", ui); return
    if "data" in q or "hoje" in q:
        d = datetime.datetime.now()
        speak(f"Today is {d.strftime('%A, %B %d, %Y')}, sir.", ui); return

    # ── STATUS ───────────────────────────────────────────
    if "status" in q or "sistema" in q or "diagnóstico" in q:
        i = sys_info()
        speak(f"System diagnostics: CPU at {i['cpu']}, RAM at {i['ram']}. "
              f"All systems nominal, sir.", ui)
        ui.update_stats(i); return

    # ── MODOS ────────────────────────────────────────────
    for m in ["cursor","hotkey","volume","jarvis"]:
        if f"modo {m}" in q: ui.controller.set_mode(m.upper()); return

    # ── SISTEMA ──────────────────────────────────────────
    if "desliga" in q:
        speak("Initiating shutdown sequence. Five seconds, sir.", ui)
        time.sleep(5); os.system("shutdown /s /t 1"); return
    if "reinicia" in q:
        speak("Restarting the system, sir.", ui)
        os.system("shutdown /r /t 3"); return
    if "bloqueia" in q or "trava" in q:
        speak("Locking the workstation, sir.", ui)
        try: ctypes.windll.user32.LockWorkStation()
        except: pass; return

    # ── VOLUME ───────────────────────────────────────────
    if "volume" in q:
        if any(x in q for x in ["aumenta","sobe","mais","cima"]):
            vol_ctrl('up'); speak("Volume increased, sir.", ui)
        elif any(x in q for x in ["diminui","baixa","menos"]):
            vol_ctrl('dn'); speak("Volume decreased, sir.", ui)
        elif any(x in q for x in ["muta","silencia","mudo"]):
            vol_ctrl('mu'); speak("Audio muted, sir.", ui)
        return

    # ── SITES WEB ────────────────────────────────────────
    for k,(url,name) in SITES.items():
        if k in q:
            frase = q.replace(k,"").replace("abre","").replace("pesquisa","").strip()
            full  = url
            if frase and k=="youtube":
                full = f"https://www.youtube.com/results?search_query={frase.replace(' ','+')}"
            elif frase and k=="google":
                full = f"https://www.google.com/search?q={frase.replace(' ','+')}"
            if WB_OK: wb.open(full)
            speak(f"Opening {name}, sir.", ui); return

    # ── SPOTIFY ──────────────────────────────────────────
    if "spotify" in q:
        try: os.startfile("spotify:")
        except:
            if WB_OK: wb.open("https://open.spotify.com")
        speak("Opening Spotify, sir.", ui); return

    # ── APPS LOCAIS ──────────────────────────────────────
    local_apps = {
        "discord":       os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
        "notepad":       "notepad.exe",
        "bloco de notas":"notepad.exe",
        "calculadora":   "calc.exe",
        "paint":         "mspaint.exe",
        "explorer":      "explorer.exe",
        "vs code":       os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        "vscode":        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        "gerenciador":   "taskmgr.exe",
    }
    for k,exe in local_apps.items():
        if k in q:
            try: subprocess.Popen([exe])
            except: pass
            speak(f"Launching {k}, sir.", ui); return

    # ── SCREENSHOT ───────────────────────────────────────
    if "screenshot" in q or "print" in q or "captura" in q:
        if AG_OK:
            try:
                p=os.path.join(Path.home(),"Pictures",
                    f"jarvis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                pyautogui.screenshot(p)
                speak("Screenshot captured and saved to your Pictures folder, sir.", ui)
                ui.add_log(f"📸 {p}","info")
            except: speak("Unable to capture screenshot, sir.", ui)
        return

    # ── TIMER ────────────────────────────────────────────
    if "timer" in q or "alarme" in q or "cronômetro" in q:
        nums = [int(s) for s in q.split() if s.isdigit()]
        if nums:
            secs = nums[0]*60 if "minuto" in q else nums[0]
            unit = "minutes" if "minuto" in q else "seconds"
            speak(f"Timer set for {nums[0]} {unit}, sir.", ui)
            def _t():
                time.sleep(secs)
                speak("Your timer has elapsed, sir.", ui)
            threading.Thread(target=_t,daemon=True).start()
        else:
            speak("Please specify the timer duration, sir.", ui)
        return

    # ── IP ───────────────────────────────────────────────
    if "meu ip" in q or "qual meu ip" in q:
        try:
            ip=socket.gethostbyname(socket.gethostname())
            speak(f"Your local IP address is {ip}, sir.", ui)
        except: speak("Unable to retrieve IP address, sir.", ui)
        return

    # ── SAIR ─────────────────────────────────────────────
    if "sair" in q or "fechar jarvis" in q or "encerra" in q:
        speak("Shutting down JARVIS. It has been a pleasure, sir.", ui)
        time.sleep(2); ui.root.destroy(); return

    # ── FALLBACK IA ──────────────────────────────────────
    speak(jarvis_response(q), ui)


# ═══════════════════════════════════════════════════════════
# RECONHECIMENTO DE VOZ  (PT-BR → responde em inglês)
# ═══════════════════════════════════════════════════════════
def listen_loop(ui):
    if not SR_OK:
        ui.add_log("⚠ SpeechRecognition não instalado.", "erro"); return

    r = sr.Recognizer()
    r.energy_threshold       = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold        = 0.6   # detecta fim de fala mais rápido

    ativo    = False
    t_ativo  = 0
    cooldown = 0.0   # evita eco da própria voz

    ui.add_log("🎙 Microfone ativo. Diga 'JARVIS' para ativar.", "info")

    while True:
        try:
            # Não escuta enquanto JARVIS está falando (evita eco)
            if pygame.mixer.music.get_busy() if PG_OK else False:
                time.sleep(0.1); continue
            if time.time() < cooldown:
                time.sleep(0.1); continue

            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.2)
                audio = r.listen(src, timeout=4, phrase_time_limit=8)

            q = r.recognize_google(audio, language="pt-BR").lower()
            ui.add_log(f"VOCÊ › {q}", "user")
            now = time.time()

            # ── WAKE WORD ─────────────────────────────────
            if "jarvis" in q:
                ativo   = True
                t_ativo = now
                ui.add_log("⚡ WAKE WORD detectada!", "alerta")
                speak("Yes, sir.", ui)
                cooldown = time.time() + 2.5  # espera a voz terminar
                continue

            # ── COMANDO (dentro da janela ativa) ──────────
            if ativo and (now - t_ativo < 15):
                # Fala o reconhecimento da intenção ANTES de executar
                en_resp = jarvis_response(q)
                speak(en_resp, ui)
                cooldown = time.time() + 2.0
                threading.Thread(target=cmd, args=(q, ui), daemon=True).start()
                t_ativo = time.time()
            else:
                ativo = False

        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# CALCULADORA WIDGET
# ═══════════════════════════════════════════════════════════
class CalcWidget(tk.Frame):
    BG="#050d1a"; AC="#00c8ff"; AC2="#003d52"; TX="#90d8f0"; DIM="#1a3040"
    FM=("Consolas",8); FB=("Consolas",8,"bold")

    def __init__(self, parent, **kw):
        super().__init__(parent,bg=self.BG,highlightbackground=self.AC2,highlightthickness=1,**kw)
        self._e=tk.StringVar(value=""); self._r=tk.StringVar(value="0")
        tk.Label(self,text="◈ CALC",fg=self.AC,bg=self.BG,font=self.FB).pack(anchor="w",padx=6,pady=(4,1))
        disp=tk.Frame(self,bg=self.AC2); disp.pack(fill="x",padx=4)
        tk.Label(disp,textvariable=self._e,fg=self.DIM,bg=self.BG,font=self.FM,anchor="e").pack(fill="x",padx=3)
        tk.Label(disp,textvariable=self._r,fg=self.AC,bg=self.BG,font=("Consolas",13,"bold"),anchor="e").pack(fill="x",padx=3)
        p=tk.Frame(self,bg=self.BG); p.pack(padx=4,pady=(2,4))
        for ri,row in enumerate([["C","←","%","÷"],["7","8","9","×"],["4","5","6","−"],["1","2","3","+"],[" ","0",".","="]]):
            for ci,k in enumerate(row):
                tk.Button(p,text=k,width=3,height=1,
                          bg=self.AC2 if k=="=" else self.BG,
                          fg=self.AC  if k in "÷×−+=C←%" else self.TX,
                          font=self.FB,activebackground=self.AC2,relief="flat",
                          highlightbackground=self.DIM,highlightthickness=1,cursor="hand2",
                          command=lambda l=k:self._press(l)).grid(row=ri,column=ci,padx=1,pady=1)
        self._b=""

    def _press(self,k):
        b=self._b
        if k=="C": b=""; self._r.set("0"); self._e.set("")
        elif k=="←": b=b[:-1]
        elif k=="=":
            if b:
                try:
                    rv=eval(b.replace("÷","/").replace("×","*").replace("−","-"),{"__builtins__":{}},{})
                    if isinstance(rv,float) and rv.is_integer(): rv=int(rv)
                    self._e.set(b+" ="); self._r.set(str(rv)); b=str(rv)
                except ZeroDivisionError: self._r.set("÷0"); b=""
                except: self._r.set("ERR"); b=""
        elif k==" ": return
        else: b+=k
        self._b=b
        if k not in("=","C"): self._r.set(b or "0")


# ═══════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL
# ═══════════════════════════════════════════════════════════
class JarvisUI:
    BG    = "#020a14"; PANEL  = "#050d1a"; PANEL2 = "#071220"
    AC    = "#00ccff"; AC2    = "#003d52"; AC3    = "#001e2a"
    TX    = "#8ad4e8"; DIM    = "#1a3040"; DIM2   = "#0d2030"
    GREEN = "#00e87a"; RED    = "#ff2244"; YELLOW = "#ffcc00"
    ORANGE= "#ff8800"; PURPLE = "#aa44ff"; CYAN2  = "#00ffee"
    F     = ("Consolas",10); FT=("Consolas",22,"bold")
    FS    = ("Consolas",8);  FB=("Consolas",9,"bold")

    ATALHOS = {
        "🌐  WEB": [
            ("Google","google","#0066cc"),("YouTube","youtube","#cc0000"),
            ("GitHub","github","#6e40c9"),("Gmail","gmail","#d44638"),
            ("ChatGPT","chatgpt","#10a37f"),("WhatsApp","whatsapp","#25d366"),
            ("Reddit","reddit","#ff4500"),("LinkedIn","linkedin","#0077b5"),
            ("Netflix","netflix","#e50914"),("Twitch","twitch","#9146ff"),
        ],
        "🎵  MÍDIA": [
            ("Spotify","spotify","#1db954"),("YT Music","youtube music","#ff0000"),
            ("SoundCloud","soundcloud","#ff5500"),("Deezer","deezer","#a238ff"),
        ],
        "💻  APPS": [
            ("VS Code","vs code","#007acc"),("Calculadora","calculadora","#00a86b"),
            ("Notepad","notepad","#555555"),("Paint","paint","#dc143c"),
            ("Discord","discord","#5865f2"),("Explorer","explorer","#f0a500"),
            ("Task Mgr","gerenciador","#cc4400"),
        ],
        "⚙️  SISTEMA": [
            ("Status PC","status","#00ccff"),("Screenshot","screenshot","#00ffcc"),
            ("Hora","hora","#ffcc00"),("Data","data","#ff9900"),
            ("Volume +",lambda:vol_ctrl('up'),"#00cc77"),
            ("Volume -",lambda:vol_ctrl('dn'),"#cc7700"),
            ("Mute",lambda:vol_ctrl('mu'),"#cc0044"),
            ("Bloquear","bloqueia","#ff3300"),
        ],
        "🎮  JOGOS": [
            ("Steam","steam","#1b2838"),("Valorant","valorant","#ff4655"),
            ("Minecraft","minecraft","#5a8a2a"),("Epic","epic","#2563eb"),
        ],
    }

    MENU_ITEMS = [
        ("Google","google"),("YouTube","youtube"),("Spotify","spotify"),
        ("WhatsApp","whatsapp"),("VS Code","vs code"),("Status","status"),
        ("Discord","discord"),("Hora","hora"),("Screenshot","screenshot"),("Sair","sair"),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S  —  Gesture Master HUD v5.1")
        self.root.geometry("1440x860")
        self.root.resizable(True,True)
        self.root.configure(bg=self.BG)
        self.root.minsize(1100,700)

        self.menu_idx  = 0
        self._cam_on   = False
        self._ge       = GestureEngine()
        self.controller= GestureController(self)

        self._build()
        self._clock_tick()
        self._stats_tick()

        threading.Thread(target=listen_loop, args=(self,), daemon=True).start()

    # ════════════════════════════════════════════════════
    def _build(self):
        self._build_header(); self._build_modebar()
        self._build_body();   self._build_statusbar()

    # ── HEADER ──────────────────────────────────────────
    def _build_header(self):
        h=tk.Frame(self.root,bg=self.BG); h.pack(fill="x",padx=14,pady=(8,0))
        tk.Label(h,text="J.A.R.V.I.S",fg=self.AC,bg=self.BG,font=self.FT).pack(side="left")
        tk.Label(h,text=" Gesture Master HUD v5.1  —  JARVIS Voice",fg=self.DIM,
                 bg=self.BG,font=("Consolas",8)).pack(side="left",pady=(10,0))
        self.lbl_clock=tk.Label(h,text="",fg=self.AC,bg=self.BG,font=("Consolas",20,"bold"))
        self.lbl_clock.pack(side="right")
        self.lbl_date=tk.Label(h,text="",fg=self.DIM,bg=self.BG,font=self.FS)
        self.lbl_date.pack(side="right",padx=10)
        tk.Frame(self.root,bg=self.AC2,height=1).pack(fill="x",padx=14,pady=(3,2))

    # ── BARRA MODOS ─────────────────────────────────────
    def _build_modebar(self):
        mb=tk.Frame(self.root,bg=self.BG); mb.pack(fill="x",padx=14,pady=(0,3))
        tk.Label(mb,text="MODO:",fg=self.DIM,bg=self.BG,font=("Consolas",8)).pack(side="left",padx=(2,6))
        mode_def={"CURSOR":(self.AC,""),"HOTKEY":(self.YELLOW,""),"VOLUME":(self.GREEN,""),"JARVIS":(self.PURPLE,"")}
        self._mode_frames={}
        for m,(color,_) in mode_def.items():
            f=tk.Frame(mb,bg=self.DIM2,padx=1,pady=1); f.pack(side="left",padx=2)
            lbl=tk.Label(f,text=f"  {m}  ",bg=self.PANEL,fg=self.DIM,
                         font=("Consolas",9,"bold"),cursor="hand2"); lbl.pack()
            lbl.bind("<Button-1>",lambda e,mo=m:self.controller.set_mode(mo))
            lbl.bind("<Enter>",lambda e,l=lbl,c=color:l.config(fg=c))
            lbl.bind("<Leave>",lambda e,l=lbl,mo=m:l.config(fg=self.AC if mo==self.controller.mode else self.DIM))
            self._mode_frames[m]=(f,lbl,color)

        # Indicador de voz / gesto
        self._gesto_var=tk.StringVar(value="GESTO: —")
        tk.Label(mb,textvariable=self._gesto_var,fg=self.ORANGE,bg=self.BG,
                 font=("Consolas",11,"bold")).pack(side="right",padx=14)

        # Indicador de voz JARVIS
        self._voice_var=tk.StringVar(value="🎙 VOZ: JARVIS (en-GB)")
        self._voice_lbl=tk.Label(mb,textvariable=self._voice_var,fg=self.GREEN,bg=self.BG,
                                  font=("Consolas",8))
        self._voice_lbl.pack(side="right",padx=8)

        # Barra volume
        self.vol_var=tk.IntVar(value=50)
        vf=tk.Frame(mb,bg=self.BG); vf.pack(side="right",padx=8)
        tk.Label(vf,text="VOL",fg=self.DIM,bg=self.BG,font=self.FS).pack(side="left")
        ttk.Progressbar(vf,variable=self.vol_var,maximum=100,length=70,mode='determinate').pack(side="left",padx=4)
        self.highlight_mode("CURSOR")
        tk.Frame(self.root,bg=self.AC2,height=1).pack(fill="x",padx=14,pady=(0,3))

    # ── CORPO ────────────────────────────────────────────
    def _build_body(self):
        body=tk.Frame(self.root,bg=self.BG); body.pack(fill="both",expand=True,padx=14)
        body.columnconfigure(0,weight=2); body.columnconfigure(1,weight=2); body.columnconfigure(2,weight=3)
        body.rowconfigure(0,weight=1)
        self._build_cam_panel(body)
        self._build_log_panel(body)
        self._build_shortcuts_panel(body)

    # ── CÂMERA ───────────────────────────────────────────
    def _build_cam_panel(self, parent):
        col=tk.Frame(parent,bg=self.BG); col.grid(row=0,column=0,sticky="nsew",padx=(0,5))
        col.rowconfigure(0,weight=3); col.rowconfigure(1,weight=1); col.rowconfigure(2,weight=1)
        col.columnconfigure(0,weight=1)

        cf=tk.Frame(col,bg=self.PANEL,highlightbackground=self.AC2,highlightthickness=1)
        cf.grid(row=0,column=0,sticky="nsew",pady=(0,4))
        cam_hdr=tk.Frame(cf,bg=self.PANEL); cam_hdr.pack(fill="x",padx=8,pady=(5,2))
        tk.Label(cam_hdr,text="◈  CÂMERA",fg=self.AC,bg=self.PANEL,font=self.FB).pack(side="left")
        self._cam_st=tk.StringVar(value="● OFF")
        self._cam_st_lbl=tk.Label(cam_hdr,textvariable=self._cam_st,fg=self.RED,bg=self.PANEL,font=self.FS)
        self._cam_st_lbl.pack(side="right")
        self._cam_lbl=tk.Label(cf,bg="#000000",
                                text="[ CÂMERA DESLIGADA ]\n\nClique ATIVAR para iniciar\nreconhecimento gestual",
                                fg=self.DIM,font=("Consolas",10))
        self._cam_lbl.pack(fill="both",expand=True,padx=6,pady=4)
        ctrl=tk.Frame(cf,bg=self.PANEL); ctrl.pack(fill="x",padx=8,pady=(0,6))
        self._cam_btn=tk.Button(ctrl,text="  ▶  ATIVAR  ",bg=self.AC2,fg=self.AC,font=self.FB,
                                 relief="flat",cursor="hand2",
                                 activebackground=self.AC,activeforeground=self.BG,
                                 command=self._toggle_cam)
        self._cam_btn.pack(side="left",ipady=3)
        tk.Label(ctrl,text="Smooth:",fg=self.DIM,bg=self.PANEL,font=self.FS).pack(side="left",padx=(8,2))
        self._sm_var=tk.DoubleVar(value=0.30)
        tk.Scale(ctrl,from_=0.05,to=1.0,resolution=0.05,variable=self._sm_var,
                 orient="horizontal",length=70,bg=self.PANEL,fg=self.AC,troughcolor=self.DIM,
                 highlightthickness=0,showvalue=False,
                 command=lambda v:setattr(self.controller,'_SMTH',float(v))).pack(side="left")

        # Referência de gestos
        leg=tk.Frame(col,bg=self.PANEL,highlightbackground=self.AC2,highlightthickness=1)
        leg.grid(row=1,column=0,sticky="nsew",pady=(0,4))
        tk.Label(leg,text="◈  REFERÊNCIA RÁPIDA",fg=self.AC,bg=self.PANEL,font=self.FB).pack(anchor="w",padx=8,pady=(5,2))
        ref_data=[
            ("CURSOR",self.AC,[("1 dedo","mover cursor"),("✌ 2 dedos","scroll"),
                                ("punho+mv","arrastar janela"),("pinça","clique"),
                                ("palma 0.7s","clique direito")]),
            ("HOTKEY",self.YELLOW,[("1 dedo","Alt+Tab"),("2 dedos","Win+D"),
                                    ("3 dedos","Win+Tab"),("4 dedos","screenshot"),
                                    ("punho","Alt+F4"),("palma","snap janela")]),
            ("VOLUME",self.GREEN,[("2 mãos dist","volume"),("1 dedo dir","vol +"),("punho dir","mute")]),
            ("JARVIS",self.PURPLE,[("1↑","subir"),("2↓","descer"),("3","confirmar"),("palma","reset")]),
            ("TROCA",self.ORANGE,[("esq 1","CURSOR"),("esq 2","HOTKEY"),("esq 3","VOLUME"),("esq palma","JARVIS")]),
        ]
        ref_txt=tk.Text(leg,bg=self.PANEL,fg=self.TX,font=("Consolas",7),relief="flat",wrap="word")
        ref_txt.pack(fill="both",expand=True,padx=6,pady=(0,5))
        ref_txt.tag_config("g",foreground=self.ORANGE); ref_txt.tag_config("a",foreground=self.GREEN)
        for mname,col_m,items in ref_data:
            ref_txt.insert("end",f"[{mname}]\n"); ref_txt.tag_add(mname,ref_txt.index("end-2l"),ref_txt.index("end-1l"))
            ref_txt.tag_config(mname,foreground=col_m,font=("Consolas",8,"bold"))
            for g,a in items:
                ref_txt.insert("end",f"  {g} ","g"); ref_txt.insert("end",f"→ {a}\n","a")
        ref_txt.config(state="disabled")

        # Menu gestual
        mf=tk.Frame(col,bg=self.PANEL,highlightbackground=self.AC2,highlightthickness=1)
        mf.grid(row=2,column=0,sticky="nsew")
        tk.Label(mf,text="◈  MENU GESTUAL  (modo JARVIS)",fg=self.AC,bg=self.PANEL,font=self.FB).pack(anchor="w",padx=8,pady=(5,2))
        tk.Label(mf,text="1↑  2↓  3=confirmar  palma=reset",fg=self.DIM,bg=self.PANEL,font=("Consolas",7)).pack(anchor="w",padx=8)
        mf2=tk.Frame(mf,bg=self.PANEL); mf2.pack(fill="both",expand=True,padx=6,pady=(2,5))
        self._menu_btns=[]
        COLS=2
        for idx,(label,mc) in enumerate(self.MENU_ITEMS):
            r2,c2=divmod(idx,COLS)
            btn=tk.Button(mf2,text=label,bg=self.PANEL,fg=self.TX,font=("Consolas",8),
                           relief="flat",cursor="hand2",activebackground=self.AC2,
                           activeforeground=self.AC,anchor="w",
                           command=lambda x=mc:self._run(x))
            btn.grid(row=r2,column=c2,padx=2,pady=1,sticky="ew")
            mf2.columnconfigure(c2,weight=1)
            self._menu_btns.append(btn)
        self.refresh_menu()

    # ── LOG ──────────────────────────────────────────────
    def _build_log_panel(self, parent):
        col=tk.Frame(parent,bg=self.BG); col.grid(row=0,column=1,sticky="nsew",padx=(0,5))
        col.rowconfigure(0,weight=1); col.columnconfigure(0,weight=1)
        lf=tk.Frame(col,bg=self.PANEL,highlightbackground=self.AC2,highlightthickness=1)
        lf.grid(row=0,column=0,sticky="nsew")
        hdr=tk.Frame(lf,bg=self.PANEL); hdr.pack(fill="x",padx=8,pady=(6,2))
        tk.Label(hdr,text="◈  LOG DE COMUNICAÇÕES",fg=self.AC,bg=self.PANEL,font=self.FB).pack(side="left")
        tk.Button(hdr,text="limpar",bg=self.PANEL,fg=self.DIM,font=self.FS,relief="flat",cursor="hand2",
                  command=lambda:(self.log.config(state="normal"),self.log.delete("1.0","end"),self.log.config(state="disabled"))
                  ).pack(side="right")
        self.log=tk.Text(lf,bg=self.PANEL,fg=self.TX,font=("Consolas",10),
                          insertbackground=self.AC,relief="flat",wrap="word",selectbackground=self.AC2)
        self.log.pack(fill="both",expand=True,padx=6,pady=(0,4))
        for tag,color in [("jarvis",self.AC),("user",self.GREEN),("gesto",self.ORANGE),
                           ("alerta",self.YELLOW),("erro",self.RED),("info",self.DIM)]:
            self.log.tag_config(tag,foreground=color)
        self.log.config(state="disabled")
        inp=tk.Frame(lf,bg=self.PANEL); inp.pack(fill="x",padx=6,pady=(0,6))
        tk.Label(inp,text="›",fg=self.AC,bg=self.PANEL,font=("Consolas",14,"bold")).pack(side="left",padx=(0,4))
        self.entry=tk.Entry(inp,bg=self.AC3,fg=self.AC,insertbackground=self.AC,
                             font=("Consolas",10),relief="flat",highlightbackground=self.AC2,highlightthickness=1)
        self.entry.pack(side="left",fill="x",expand=True,ipady=4)
        self.entry.bind("<Return>",self._send)
        tk.Button(inp,text="SEND",bg=self.AC2,fg=self.AC,font=self.FB,relief="flat",cursor="hand2",
                  padx=8,activebackground=self.AC,activeforeground=self.BG,command=self._send
                  ).pack(side="left",padx=(4,0),ipady=4)

    # ── PAINEL ATALHOS ───────────────────────────────────
    def _build_shortcuts_panel(self, parent):
        outer=tk.Frame(parent,bg=self.BG); outer.grid(row=0,column=2,sticky="nsew")
        outer.rowconfigure(0,weight=1); outer.columnconfigure(0,weight=1)
        cv=tk.Canvas(outer,bg=self.BG,highlightthickness=0,bd=0)
        sb=tk.Scrollbar(outer,orient="vertical",command=cv.yview,bg=self.BG,troughcolor=self.DIM2)
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); cv.pack(side="left",fill="both",expand=True)
        inner=tk.Frame(cv,bg=self.BG)
        cw=cv.create_window((0,0),window=inner,anchor="nw")
        inner.bind("<Configure>",lambda e:cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",lambda e:cv.itemconfig(cw,width=e.width))
        cv.bind_all("<MouseWheel>",lambda e:cv.yview_scroll(int(-1*(e.delta/120)),"units"))

        # ─ Painel de voz JARVIS ─
        vp=tk.Frame(inner,bg=self.PANEL,highlightbackground=self.PURPLE,highlightthickness=1)
        vp.pack(fill="x",pady=(0,5))
        tk.Label(vp,text="◈  VOZ JARVIS",fg=self.PURPLE,bg=self.PANEL,font=self.FB).pack(anchor="w",padx=8,pady=(5,2))
        vp_inner=tk.Frame(vp,bg=self.PANEL); vp_inner.pack(fill="x",padx=8,pady=(0,6))
        voice_info=[
            ("Motor:",  "Microsoft Edge Neural TTS"),
            ("Voz:",    "en-GB-RyanNeural"),
            ("Estilo:", "Britânico formal — JARVIS"),
            ("Pitch:",  f"{JARVIS_PITCH}  Rate: {JARVIS_RATE}"),
            ("Wake:",   "Diga 'JARVIS' para ativar"),
            ("Cache:",  f"{len(PRECACHE_PHRASES)} frases pré-geradas"),
        ]
        for lbl,val in voice_info:
            row=tk.Frame(vp_inner,bg=self.PANEL); row.pack(fill="x",pady=1)
            tk.Label(row,text=lbl,fg=self.DIM,bg=self.PANEL,font=("Consolas",7),width=8,anchor="w").pack(side="left")
            tk.Label(row,text=val,fg=self.PURPLE,bg=self.PANEL,font=("Consolas",7),anchor="w").pack(side="left")

        # Botão testar voz
        tk.Button(vp, text="▶  TESTAR VOZ JARVIS",
                  bg=self.DIM2, fg=self.PURPLE, font=("Consolas",8,"bold"),
                  relief="flat", cursor="hand2",
                  activebackground=self.PURPLE, activeforeground=self.BG,
                  command=lambda: threading.Thread(
                      target=speak, args=("All systems are operational, sir. JARVIS online.", self),
                      daemon=True).start()
                  ).pack(fill="x", padx=8, pady=(0,6))

        # ─ Stats ─
        sf=tk.Frame(inner,bg=self.PANEL,highlightbackground=self.AC2,highlightthickness=1)
        sf.pack(fill="x",pady=(0,5))
        tk.Label(sf,text="◈  STATUS DO SISTEMA",fg=self.AC,bg=self.PANEL,font=self.FB).pack(anchor="w",padx=8,pady=(5,2))
        self.stat_vars={}
        sg=tk.Frame(sf,bg=self.PANEL); sg.pack(fill="x",padx=8,pady=(0,5))
        for i,(lbl,key) in enumerate([("CPU","cpu"),("RAM","ram"),("DISCO","disk"),("BAT","bat"),("IP","ip")]):
            r2,c2=divmod(i,2)
            f2=tk.Frame(sg,bg=self.DIM2); f2.grid(row=r2,column=c2,padx=2,pady=2,sticky="ew")
            sg.columnconfigure(c2,weight=1)
            tk.Label(f2,text=lbl,fg=self.DIM,bg=self.DIM2,font=("Consolas",7)).pack(anchor="w",padx=4,pady=(2,0))
            var=tk.StringVar(value="…")
            tk.Label(f2,textvariable=var,fg=self.AC,bg=self.DIM2,font=("Consolas",9,"bold")).pack(anchor="w",padx=4,pady=(0,2))
            self.stat_vars[key]=var

        CalcWidget(inner).pack(fill="x",pady=(0,5))
        for cat,items in self.ATALHOS.items():
            self._build_category(inner,cat,items)

    def _build_category(self, parent, cat_name, items):
        sec=tk.Frame(parent,bg=self.PANEL,highlightbackground=self.AC2,highlightthickness=1)
        sec.pack(fill="x",pady=(0,5))
        hdr=tk.Frame(sec,bg=self.AC2,cursor="hand2"); hdr.pack(fill="x")
        lbl=tk.Label(hdr,text=cat_name,fg=self.AC,bg=self.AC2,font=self.FB); lbl.pack(side="left",padx=8,pady=4)
        arr=tk.Label(hdr,text="▲",fg=self.DIM,bg=self.AC2,font=("Consolas",8)); arr.pack(side="right",padx=8)
        gf=tk.Frame(sec,bg=self.PANEL); gf.pack(fill="x",padx=6,pady=4)
        expanded=[True]
        COLS=3
        for idx,(name,action,color) in enumerate(items):
            r2,c2=divmod(idx,COLS)
            fn=action if callable(action) else lambda a=action:self._run(a)
            btn=tk.Button(gf,text=name,bg=self.DIM2,fg=self.TX,font=("Consolas",8),
                           relief="flat",cursor="hand2",anchor="w",pady=3,
                           activebackground=color,activeforeground="#ffffff",command=fn)
            btn.grid(row=r2,column=c2,padx=2,pady=2,sticky="ew")
            gf.columnconfigure(c2,weight=1)
            btn.bind("<Enter>",lambda e,b=btn,cl=color:b.config(bg=cl,fg="#ffffff"))
            btn.bind("<Leave>",lambda e,b=btn:b.config(bg=self.DIM2,fg=self.TX))
        def toggle(_=None):
            if expanded[0]: gf.pack_forget(); arr.config(text="▼"); expanded[0]=False
            else:            gf.pack(fill="x",padx=6,pady=4); arr.config(text="▲"); expanded[0]=True
        for w in (hdr,lbl,arr): w.bind("<Button-1>",toggle)

    # ── STATUS BAR ───────────────────────────────────────
    def _build_statusbar(self):
        tk.Frame(self.root,bg=self.AC2,height=1).pack(fill="x",padx=14,pady=(3,0))
        sb=tk.Frame(self.root,bg=self.BG); sb.pack(fill="x",padx=14,pady=(2,4))
        self._status_var=tk.StringVar(value="◉  SISTEMA ONLINE  |  CÂMERA INATIVA")
        tk.Label(sb,textvariable=self._status_var,fg=self.GREEN,bg=self.BG,font=("Consolas",8)).pack(side="left")
        quick_kb=[
            ("Alt+Tab",lambda:AG_OK and pyautogui.hotkey('alt','tab')),
            ("Win+D",  lambda:AG_OK and pyautogui.hotkey('win','d')),
            ("Win+L",  lambda:ctypes.windll.user32.LockWorkStation()),
            ("Vol+",   lambda:vol_ctrl('up')),("Vol-",lambda:vol_ctrl('dn')),
            ("Mute",   lambda:vol_ctrl('mu')),
            ("Print",  lambda:AG_OK and pyautogui.press('printscreen')),
        ]
        for label,fn in quick_kb:
            b=tk.Button(sb,text=label,bg=self.DIM2,fg=self.DIM,font=("Consolas",7),
                        relief="flat",cursor="hand2",padx=5,
                        activebackground=self.AC2,activeforeground=self.AC,
                        command=lambda f=fn:threading.Thread(target=f,daemon=True).start())
            b.pack(side="right",padx=1,ipady=2)
            b.bind("<Enter>",lambda e,btn=b:btn.config(fg=self.AC))
            b.bind("<Leave>",lambda e,btn=b:btn.config(fg=self.DIM))

    # ════════════════════════════════════════════════════
    # CÂMERA LOOP
    # ════════════════════════════════════════════════════
    def _toggle_cam(self):
        if not CV2_OK: self.add_log("⚠ mediapipe/opencv não instalados!","erro"); return
        if not self._cam_on: self._start_cam()
        else: self._stop_cam()

    def _start_cam(self):
        if not self._ge.start(): self.add_log("⚠ Webcam não encontrada.","erro"); return
        self._cam_on=True
        self._cam_btn.config(text="  ■  PARAR  ",bg="#1a0008",fg=self.RED,
                              activebackground=self.RED,activeforeground=self.BG)
        self._cam_st.set("● ON"); self._cam_st_lbl.config(fg=self.GREEN)
        self._status_var.set("◉  CÂMERA ATIVA  —  RECONHECENDO GESTOS")
        self.add_log("✔ Câmera ativada.","gesto")
        speak("Camera activated. Gesture control is now online, sir.",self)
        threading.Thread(target=self._cam_loop,daemon=True).start()

    def _stop_cam(self):
        self._cam_on=False; self._ge.stop()
        self._cam_btn.config(text="  ▶  ATIVAR  ",bg=self.AC2,fg=self.AC,
                              activebackground=self.AC,activeforeground=self.BG)
        self._cam_st.set("● OFF"); self._cam_st_lbl.config(fg=self.RED)
        self._status_var.set("◉  SISTEMA ONLINE  |  CÂMERA INATIVA")
        self._cam_lbl.config(image="",text="[ CÂMERA DESLIGADA ]",fg=self.DIM)
        self._gesto_var.set("GESTO: —")
        self.add_log("■ Câmera desligada.","info")
        speak("Camera deactivated, sir.",self)

    def _cam_loop(self):
        while self._cam_on:
            frame,right,left,cr,cl=self._ge.read()
            if frame is None: time.sleep(0.04); continue
            parts=[]
            if right: parts.append(f"DIR:{right['g']}")
            if left:  parts.append(f"ESQ:{left['g']}")
            self.root.after(0,lambda p=" | ".join(parts) if parts else "—":
                            self._gesto_var.set(f"GESTO: {p}"))
            self.controller.process(right,left,cr,cl)
            try:
                sm=cv2.resize(frame,(360,260))
                sm_rgb=cv2.cvtColor(sm,cv2.COLOR_BGR2RGB)
                img=tk.PhotoImage(data=cv2.imencode('.ppm',cv2.cvtColor(sm_rgb,cv2.COLOR_RGB2BGR))[1].tobytes())
                self.root.after(0,lambda i=img:self._upd_cam(i))
            except: pass
            time.sleep(0.025)

    def _upd_cam(self,img):
        try: self._cam_lbl.config(image=img,text=""); self._cam_lbl._img=img
        except: pass

    # ════════════════════════════════════════════════════
    # MENU GESTUAL
    # ════════════════════════════════════════════════════
    def refresh_menu(self):
        for i,btn in enumerate(self._menu_btns):
            if i==self.menu_idx:
                btn.config(bg=self.AC2,fg=self.AC,font=("Consolas",8,"bold"),relief="groove")
            else:
                btn.config(bg=self.PANEL,fg=self.TX,font=("Consolas",8),relief="flat")

    def menu_up(self):
        self.menu_idx=(self.menu_idx-1)%len(self.MENU_ITEMS); self.refresh_menu()

    def menu_down(self):
        self.menu_idx=(self.menu_idx+1)%len(self.MENU_ITEMS); self.refresh_menu()

    def menu_confirm(self):
        label,mc=self.MENU_ITEMS[self.menu_idx]
        self.add_log(f"GESTO CONFIRM › {label}","gesto")
        self._run(mc)

    # ════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ════════════════════════════════════════════════════
    def highlight_mode(self,active):
        for m,(f,lbl,color) in self._mode_frames.items():
            if m==active: f.config(bg=color); lbl.config(bg=color,fg=self.BG)
            else:         f.config(bg=self.DIM2); lbl.config(bg=self.PANEL,fg=self.DIM)

    def update_stats(self,info):
        for k in ["cpu","ram","disk","bat","ip"]:
            if k in self.stat_vars and k in info:
                self.stat_vars[k].set(info[k])

    def add_log(self,text,tag=None):
        def _i():
            self.log.config(state="normal")
            ts=datetime.datetime.now().strftime("%H:%M:%S")
            self.log.insert("end",f"[{ts}]  ","info")
            self.log.insert("end",text+"\n",tag or "")
            self.log.see("end"); self.log.config(state="disabled")
        self.root.after(0,_i)

    def _send(self,event=None):
        q=self.entry.get().strip()
        if not q: return
        self.entry.delete(0,"end")
        self.add_log(f"VOCÊ › {q}","user")
        resp=jarvis_response(q)
        speak(resp,self)
        threading.Thread(target=cmd,args=(q,self),daemon=True).start()

    def _run(self,action):
        if callable(action): threading.Thread(target=action,daemon=True).start()
        else:
            self.add_log(f"CMD › {action}","user")
            resp=jarvis_response(action)
            speak(resp,self)
            threading.Thread(target=cmd,args=(action,self),daemon=True).start()

    def _clock_tick(self):
        now=datetime.datetime.now()
        self.lbl_clock.config(text=now.strftime("%H:%M:%S"))
        self.lbl_date.config( text=now.strftime("%d/%m/%Y — %A"))
        self.root.after(1000,self._clock_tick)

    def _stats_tick(self):
        info=sys_info(); self.update_stats(info)
        self.root.after(5000,self._stats_tick)

    # ════════════════════════════════════════════════════
    def run(self):
        self.add_log("⏳ Pré-gerando cache de voz JARVIS... aguarde.", "alerta")
        def _boot():
            # Espera o cache inicializar (máx 15s)
            _speak_ready.wait(timeout=15)
            speak("JARVIS Gesture Master online. All modules loaded. Ready for your command, sir.", self)
        threading.Thread(target=_boot, daemon=True).start()
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    JarvisUI().run()
