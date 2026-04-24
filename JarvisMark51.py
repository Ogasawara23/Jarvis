"""
╔══════════════════════════════════════════════════════════════════════╗
║        J.A.R.V.I.S  —  GESTURE MASTER HUD v5.2                     ║
║  ARC REACTOR SPLASH  +  UI Circular JARVIS  +  Comandos completos   ║
╠══════════════════════════════════════════════════════════════════════╣
║  INSTALAÇÃO COMPLETA:                                                ║
║    pip install mediapipe opencv-python numpy pyautogui               ║
║    pip install SpeechRecognition psutil pywin32 pycaw comtypes       ║
║    pip install edge-tts pygame                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  VOZ:                                                                ║
║    • Motor: Microsoft Edge TTS Neural (GRÁTIS, sem API key)          ║
║    • Voz: en-GB-RyanNeural  — britânico, grave, formal               ║
║    • Pitch: -8Hz  Rate: -5%  → soa como o JARVIS do filme            ║
║    • Cache: respostas comuns pré-geradas para resposta INSTANTÂNEA   ║
╠══════════════════════════════════════════════════════════════════════╣
║  WAKE WORD: fale "JARVIS" → responde "Yes, sir." imediatamente       ║
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
CACHE_DIR = Path(tempfile.gettempdir()) / "jarvis_voice_cache"
CACHE_DIR.mkdir(exist_ok=True)

JARVIS_VOICE  = "en-GB-RyanNeural"
JARVIS_RATE   = "-5%"
JARVIS_PITCH  = "-8Hz"

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
    communicate = edge_tts.Communicate(text, JARVIS_VOICE, rate=JARVIS_RATE, pitch=JARVIS_PITCH)
    await communicate.save(str(path))

def _ensure_cached(text: str) -> Path:
    path = _cache_path(text)
    if not path.exists():
        try:
            asyncio.run(_generate_audio(text, path))
        except Exception as e:
            return None
    return path

def _precache_worker():
    for phrase in PRECACHE_PHRASES:
        _ensure_cached(phrase)
    _speak_ready.set()

def _play_audio(path: Path):
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
    while True:
        text = _voz_q.get()
        try:
            if EDGE_OK and PG_OK:
                path = _ensure_cached(text)
                if path:
                    _play_audio(path)
                else:
                    _pyttsx3_fallback(text)
            else:
                _pyttsx3_fallback(text)
        except Exception:
            pass
        _voz_q.task_done()

def _pyttsx3_fallback(text: str):
    try:
        import pyttsx3
        e = pyttsx3.init()
        e.setProperty('rate', 160)
        for v in e.getProperty('voices'):
            if 'english' in v.name.lower():
                e.setProperty('voice', v.id); break
        e.say(text); e.runAndWait()
    except: pass

threading.Thread(target=_voz_worker, daemon=True).start()
threading.Thread(target=_precache_worker, daemon=True).start()

def speak(text: str, ui=None):
    if ui:
        ui.add_log(f"JARVIS › {text}", "jarvis")
    _voz_q.put(text)

PTBR_TO_EN = {
    "jarvis": "Yes, sir.",
    "sim": "Of course, sir.",
    "ok": "Right away, sir.",
    "obrigado": "My pleasure, sir.",
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
    "status": "Fetching system diagnostics, sir.",
    "hora": None,
    "data": None,
    "screenshot": "Screenshot captured and saved to your Pictures folder, sir.",
    "bloqueia": "Locking the workstation, sir.",
    "desliga": "Initiating shutdown sequence in five seconds, sir.",
    "reinicia": "Restarting the system, sir.",
    "volume": None,
    "modo cursor": "Switching to cursor mode, sir.",
    "modo hotkey": "Switching to hotkey mode, sir.",
    "modo volume": "Switching to volume mode, sir.",
    "modo jarvis": "Switching to JARVIS mode, sir.",
    "sair": "Shutting down JARVIS. Good day, sir.",
    "fechar jarvis": "Shutting down JARVIS. Good day, sir.",
}

def jarvis_response(query_ptbr: str) -> str:
    q = query_ptbr.lower().strip()
    for key, resp in PTBR_TO_EN.items():
        if key in q and resp:
            return resp
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

    if "hora" in q or "que horas" in q:
        agora = datetime.datetime.now().strftime('%H:%M')
        speak(f"The current time is {agora}, sir.", ui); return
    if "data" in q or "hoje" in q:
        d = datetime.datetime.now()
        speak(f"Today is {d.strftime('%A, %B %d, %Y')}, sir.", ui); return
    if "status" in q or "sistema" in q or "diagnóstico" in q:
        i = sys_info()
        speak(f"System diagnostics: CPU at {i['cpu']}, RAM at {i['ram']}. All systems nominal, sir.", ui)
        ui.update_stats(i); return
    for m in ["cursor","hotkey","volume","jarvis"]:
        if f"modo {m}" in q: ui.controller.set_mode(m.upper()); return
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
    if "volume" in q:
        if any(x in q for x in ["aumenta","sobe","mais","cima"]):
            vol_ctrl('up'); speak("Volume increased, sir.", ui)
        elif any(x in q for x in ["diminui","baixa","menos"]):
            vol_ctrl('dn'); speak("Volume decreased, sir.", ui)
        elif any(x in q for x in ["muta","silencia","mudo"]):
            vol_ctrl('mu'); speak("Audio muted, sir.", ui)
        return
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
    if "spotify" in q:
        try: os.startfile("spotify:")
        except:
            if WB_OK: wb.open("https://open.spotify.com")
        speak("Opening Spotify, sir.", ui); return
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
    if "meu ip" in q or "qual meu ip" in q:
        try:
            ip=socket.gethostbyname(socket.gethostname())
            speak(f"Your local IP address is {ip}, sir.", ui)
        except: speak("Unable to retrieve IP address, sir.", ui)
        return
    if "sair" in q or "fechar jarvis" in q or "encerra" in q:
        speak("Shutting down JARVIS. It has been a pleasure, sir.", ui)
        time.sleep(2); ui.root.destroy(); return
    speak(jarvis_response(q), ui)


# ═══════════════════════════════════════════════════════════
# RECONHECIMENTO DE VOZ
# ═══════════════════════════════════════════════════════════
def listen_loop(ui):
    if not SR_OK:
        ui.add_log("⚠ SpeechRecognition não instalado.", "erro"); return

    r = sr.Recognizer()
    r.energy_threshold        = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold         = 0.6

    ativo    = False
    t_ativo  = 0
    cooldown = 0.0

    ui.add_log("🎙 Microfone ativo. Diga 'JARVIS' para ativar.", "info")

    while True:
        try:
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
            if "jarvis" in q:
                ativo   = True
                t_ativo = now
                ui.add_log("⚡ WAKE WORD detectada!", "alerta")
                speak("Yes, sir.", ui)
                cooldown = time.time() + 2.5
                continue
            if ativo and (now - t_ativo < 15):
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
    BG="#020e1a"; AC="#00c8ff"; AC2="#003d52"; TX="#90d8f0"; DIM="#1a3040"
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
# TELA DE ABERTURA — ARC REACTOR
# ═══════════════════════════════════════════════════════════
class ArcReactorSplash:
    """Tela de abertura estilo Arc Reactor do Homem de Ferro."""

    BG    = "#000a12"
    AC    = "#00ccff"
    AC2   = "#0055aa"
    GLOW  = "#003366"
    WHITE = "#e8f4ff"

    def __init__(self, on_complete):
        self.on_complete = on_complete
        self.root = tk.Tk()
        self.root.title("JARVIS — Initializing")
        self.root.configure(bg=self.BG)
        self.root.overrideredirect(True)

        # Centraliza na tela
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W, H = 700, 600
        x = (sw - W) // 2
        y = (sh - H) // 2
        self.root.geometry(f"{W}x{H}+{x}+{y}")

        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                 bg=self.BG, highlightthickness=0)
        self.canvas.pack()

        self._W = W
        self._H = H
        self._cx = W // 2
        self._cy = H // 2 - 30
        self._t  = 0
        self._rings_alpha  = [0.0] * 6   # opacidade de cada anel
        self._phase        = 0            # 0=entrada, 1=pulso, 2=saída
        self._boot_msgs    = [
            "Initializing arc reactor...",
            "Loading neural interface...",
            "Calibrating gesture engine...",
            "Voice synthesis: ONLINE",
            "All systems nominal.",
            "Welcome back, sir.",
        ]
        self._msg_idx  = 0
        self._msg_var  = tk.StringVar(value="")
        self._progress = 0.0

        # Label de boot
        self._lbl = tk.Label(self.root, textvariable=self._msg_var,
                              fg=self.AC, bg=self.BG,
                              font=("Consolas", 10), anchor="center")
        self._lbl.place(x=W//2, y=H-80, anchor="center")

        # Label JARVIS
        self._title = tk.Label(self.root, text="J.A.R.V.I.S",
                                fg="#003344", bg=self.BG,
                                font=("Consolas", 28, "bold"))
        self._title.place(x=W//2, y=H-120, anchor="center")

        # Barra de progresso custom
        self._pbar_bg = self.canvas.create_rectangle(
            100, H-50, W-100, H-36, fill="#001122", outline="#003344", width=1)
        self._pbar_fill = self.canvas.create_rectangle(
            100, H-50, 100, H-36, fill=self.AC, outline="")
        self._pbar_glow = self.canvas.create_rectangle(
            100, H-50, 100, H-36, fill="#66ddff", outline="", stipple="gray50")

        self._draw_frame()
        self.root.after(50, self._animate)

    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, r, g, b):
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _lerp_color(self, c1, c2, t):
        r1,g1,b1 = self._hex_to_rgb(c1)
        r2,g2,b2 = self._hex_to_rgb(c2)
        t = max(0.0, min(1.0, t))
        return self._rgb_to_hex(r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t)

    def _draw_arc_reactor(self):
        """Desenha o Arc Reactor com múltiplos anéis concêntricos."""
        cx, cy = self._cx, self._cy
        c = self.canvas

        # Brilho de fundo (halo)
        for i in range(8, 0, -1):
            alpha = max(0, self._rings_alpha[0] - i * 0.04)
            r = 110 + i * 14
            col = self._lerp_color(self.BG, "#001833", alpha)
            c.create_oval(cx-r, cy-r, cx+r, cy+r, fill=col, outline="")

        # Anel externo decorativo (hexagonal-ish)
        # Simulado como círculo com traços
        rings = [
            (95, 3, "#004466", 0),
            (88, 2, "#005577", 1),
            (78, 1, "#006688", 1),
        ]
        for radius, width, color, ring_idx in rings:
            if ring_idx < len(self._rings_alpha):
                alpha = self._rings_alpha[ring_idx]
            else:
                alpha = self._rings_alpha[-1]
            col = self._lerp_color(self.BG, color, alpha)
            c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                          fill="", outline=col, width=width)

        # Segmentos do anel externo rotacionando
        seg_alpha = self._rings_alpha[2] if len(self._rings_alpha) > 2 else 0
        if seg_alpha > 0:
            num_segs = 12
            for i in range(num_segs):
                angle_start = (self._t * 0.8 + i * (360/num_segs))
                angle_end   = angle_start + 12
                intensity = (math.sin(math.radians(self._t * 3 + i * 30)) + 1) / 2
                seg_col = self._lerp_color(self.BG, self.AC, seg_alpha * intensity * 0.7)
                c.create_arc(cx-92, cy-92, cx+92, cy+92,
                             start=angle_start, extent=12,
                             fill="", outline=seg_col, width=2, style=tk.ARC)

        # Anel médio — giratório inverso
        mid_alpha = self._rings_alpha[3] if len(self._rings_alpha) > 3 else 0
        if mid_alpha > 0:
            for i in range(8):
                angle_start = (-self._t * 1.2 + i * 45)
                intensity = (math.sin(math.radians(self._t * 4 + i * 45)) + 1) / 2
                col = self._lerp_color(self.BG, "#0088cc", mid_alpha * (0.3 + intensity*0.5))
                c.create_arc(cx-65, cy-65, cx+65, cy+65,
                             start=angle_start, extent=18,
                             fill="", outline=col, width=1.5, style=tk.ARC)

        # Anel interno fixo
        inner_alpha = self._rings_alpha[4] if len(self._rings_alpha) > 4 else 0
        if inner_alpha > 0:
            col = self._lerp_color(self.BG, "#00aadd", inner_alpha)
            c.create_oval(cx-48, cy-48, cx+48, cy+48,
                          fill="", outline=col, width=2)
            col2 = self._lerp_color(self.BG, "#003355", inner_alpha)
            c.create_oval(cx-42, cy-42, cx+42, cy+42,
                          fill=col2, outline="")

        # Triângulos internos
        tri_alpha = self._rings_alpha[5] if len(self._rings_alpha) > 5 else 0
        if tri_alpha > 0:
            for ang_offset in [0, 120, 240]:
                ang = math.radians(self._t * 1.5 + ang_offset)
                r1, r2 = 30, 42
                pts = []
                for da in [-15, 0, 15]:
                    a = ang + math.radians(da)
                    pts.extend([cx + r2*math.cos(a), cy + r2*math.sin(a)])
                a2 = ang + math.radians(180)
                pts.extend([cx + r1*math.cos(a2), cy + r1*math.sin(a2)])
                col = self._lerp_color(self.BG, self.AC, tri_alpha * 0.8)
                c.create_polygon(pts, fill=col, outline="")

        # Núcleo pulsante
        core_alpha = self._rings_alpha[5] if len(self._rings_alpha) > 5 else 0
        if core_alpha > 0:
            pulse = (math.sin(math.radians(self._t * 6)) + 1) / 2
            core_r = 16 + pulse * 3
            col_core = self._lerp_color(self.BG, "#aaeeff", core_alpha * (0.7 + pulse*0.3))
            c.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r,
                          fill=col_core, outline=self.WHITE if core_alpha > 0.8 else "")
            # brilho central
            col_white = self._lerp_color(self.BG, self.WHITE, core_alpha * (0.5 + pulse*0.5))
            c.create_oval(cx-6, cy-6, cx+6, cy+6, fill=col_white, outline="")

        # Raios (spokes) do anel
        spoke_alpha = self._rings_alpha[3] if len(self._rings_alpha) > 3 else 0
        if spoke_alpha > 0:
            for i in range(6):
                ang = math.radians(self._t * 0.5 + i * 60)
                x1 = cx + 48 * math.cos(ang)
                y1 = cy + 48 * math.sin(ang)
                x2 = cx + 78 * math.cos(ang)
                y2 = cy + 78 * math.sin(ang)
                col = self._lerp_color(self.BG, self.AC, spoke_alpha * 0.6)
                c.create_line(x1, y1, x2, y2, fill=col, width=1)

        # Hexágonos externos decorativos
        if self._rings_alpha[2] > 0.3:
            hex_alpha = self._rings_alpha[2]
            for i in range(6):
                ang = math.radians(self._t * 0.3 + i * 60)
                hx = cx + 110 * math.cos(ang)
                hy = cy + 110 * math.sin(ang)
                hw = 8
                pts = []
                for j in range(6):
                    a2 = math.radians(j * 60)
                    pts.extend([hx + hw*math.cos(a2), hy + hw*math.sin(a2)])
                col = self._lerp_color(self.BG, "#0066aa", hex_alpha * 0.5)
                c.create_polygon(pts, fill="", outline=col, width=1)

    def _draw_frame(self):
        self.canvas.delete("all")

        # Fundo com gradiente radial (concêntrico)
        for i in range(20, 0, -1):
            r = i * 20
            shade = min(255, i * 4)
            bg_col = f"#{0:02x}{shade//8:02x}{shade//4:02x}"
            # Apenas se não for muito claro
            if i < 15:
                self.canvas.create_oval(
                    self._cx-r, self._cy-r, self._cx+r, self._cy+r,
                    fill="", outline=bg_col, width=1)

        self._draw_arc_reactor()

        # Recria barra de progresso
        W = self._W
        H = self._H
        self.canvas.create_rectangle(100, H-50, W-100, H-36,
                                      fill="#001122", outline="#003344", width=1)
        prog_w = int((W-200) * self._progress)
        if prog_w > 0:
            self.canvas.create_rectangle(100, H-50, 100+prog_w, H-36,
                                          fill=self.AC, outline="")
            # Brilho
            self.canvas.create_rectangle(100, H-50, 100+min(prog_w, 30), H-43,
                                          fill="#88eeff", outline="")

    def _animate(self):
        self._t += 2
        phase_dur = [60, 80, 40]  # frames por fase

        # Fase 0: entrada dos anéis
        if self._phase == 0:
            progress = min(1.0, self._t / phase_dur[0])
            # Cada anel entra em sequência
            for i in range(6):
                self._rings_alpha[i] = max(0.0, min(1.0, (progress * 6 - i) * 1.5))
            self._progress = progress * 0.5
            # Mensagens de boot
            msg_progress = int(progress * len(self._boot_msgs))
            if msg_progress < len(self._boot_msgs) and msg_progress != self._msg_idx:
                self._msg_idx = msg_progress
                self._msg_var.set(self._boot_msgs[self._msg_idx])
            # Fade do título
            title_alpha = max(0, progress - 0.5) * 2
            col = self._lerp_color(self.BG, self.AC, title_alpha)
            self._title.config(fg=col)
            if progress >= 1.0:
                self._phase = 1
                self._t = 0

        # Fase 1: pulsação completa
        elif self._phase == 1:
            progress = min(1.0, self._t / phase_dur[1])
            for i in range(6):
                self._rings_alpha[i] = 1.0
            self._progress = 0.5 + progress * 0.5
            # Última mensagem
            self._msg_var.set(self._boot_msgs[-1])
            if progress >= 1.0:
                self._phase = 2
                self._t = 0

        # Fase 2: fade out
        elif self._phase == 2:
            progress = min(1.0, self._t / phase_dur[2])
            for i in range(6):
                self._rings_alpha[i] = 1.0 - progress
            col = self._lerp_color(self.AC, self.BG, progress)
            self._title.config(fg=col)
            self._msg_var.set("")
            if progress >= 1.0:
                self.root.destroy()
                self.on_complete()
                return

        self._draw_frame()
        self.root.after(33, self._animate)  # ~30fps

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════
# CANVAS CIRCULAR JARVIS — Widget para anéis no HUD
# ═══════════════════════════════════════════════════════════
class JarvisArcCanvas(tk.Canvas):
    """Canvas com anéis JARVIS animados no painel da câmera."""

    def __init__(self, parent, size=260, **kw):
        super().__init__(parent, width=size, height=size,
                         bg="#020a14", highlightthickness=0, **kw)
        self._size = size
        self._cx   = size // 2
        self._cy   = size // 2
        self._t    = 0
        self._active = True
        self._cam_img = None
        self._animate()

    def set_image(self, img):
        self._cam_img = img
        # Quando tem câmera, desativa a animação pura
        self._active = False

    def clear_image(self):
        self._cam_img = None
        self._active = True

    def _animate(self):
        if not self._active or self._cam_img is not None:
            try: self.after(100, self._animate)
            except: pass
            return
        self._t += 2
        self._draw()
        try: self.after(40, self._animate)
        except: pass

    def _draw(self):
        if self._cam_img:
            return
        self.delete("all")
        cx, cy = self._cx, self._cy
        t = self._t

        # Fundo escuro com halo
        self.create_oval(4, 4, self._size-4, self._size-4,
                         fill="#020e1a", outline="#003344", width=1)

        # Anéis externos
        ring_data = [
            (cx-100, cy-100, cx+100, cy+100, 1, "#004455"),
            (cx-88,  cy-88,  cx+88,  cy+88,  1, "#005566"),
            (cx-76,  cy-76,  cx+76,  cy+76,  1, "#003344"),
        ]
        for x0,y0,x1,y1,w,col in ring_data:
            self.create_oval(x0,y0,x1,y1, fill="", outline=col, width=w)

        # Segmentos giratórios
        pulse = (math.sin(math.radians(t * 4)) + 1) / 2
        for i in range(10):
            ang = t * 0.9 + i * 36
            intensity = (math.sin(math.radians(t * 3 + i * 36)) + 1) / 2
            blue = int(40 + intensity * 80)
            col = f"#00{blue:02x}{min(255, blue+80):02x}"
            self.create_arc(cx-92, cy-92, cx+92, cy+92,
                            start=ang, extent=14,
                            fill="", outline=col, width=2, style=tk.ARC)

        # Anel médio — contra-rotação
        for i in range(6):
            ang = -t * 1.3 + i * 60
            i2 = (math.sin(math.radians(t * 5 + i * 60)) + 1) / 2
            b = int(60 + i2 * 120)
            col = f"#00{b:02x}cc"
            self.create_arc(cx-62, cy-62, cx+62, cy+62,
                            start=ang, extent=22,
                            fill="", outline=col, width=1, style=tk.ARC)

        # Spokes
        for i in range(6):
            ang = math.radians(t * 0.6 + i * 60)
            x1 = cx + 46 * math.cos(ang)
            y1 = cy + 46 * math.sin(ang)
            x2 = cx + 72 * math.cos(ang)
            y2 = cy + 72 * math.sin(ang)
            self.create_line(x1, y1, x2, y2, fill="#005577", width=1)

        # Triângulos internos
        for j, ang_off in enumerate([0, 120, 240]):
            ang = math.radians(t * 1.5 + ang_off)
            pts = []
            for da in [-12, 0, 12]:
                a = ang + math.radians(da)
                pts.extend([cx + 38*math.cos(a), cy + 38*math.sin(a)])
            a2 = ang + math.radians(180)
            pts.extend([cx + 22*math.cos(a2), cy + 22*math.sin(a2)])
            b = int(80 + pulse * 120)
            col = f"#00{b:02x}{min(255,b+80):02x}"
            self.create_polygon(pts, fill=col, outline="")

        # Anel interno
        self.create_oval(cx-30, cy-30, cx+30, cy+30,
                         fill="#001a2a", outline="#0077aa", width=1)

        # Núcleo pulsante
        cr = 12 + pulse * 4
        b_val = int(180 + pulse * 75)
        core_col = f"#66{b_val:02x}ff"
        self.create_oval(cx-cr, cy-cr, cx+cr, cy+cr,
                         fill=core_col, outline="#aaeeff", width=1)
        self.create_oval(cx-5, cy-5, cx+5, cy+5, fill="#ddf8ff", outline="")

        # Texto status no topo
        self.create_text(cx, 12, text="◈ GESTURE ENGINE ◈",
                         fill="#003355", font=("Consolas", 7))


# ═══════════════════════════════════════════════════════════
# INTERFACE PRINCIPAL — DESIGN CIRCULAR JARVIS
# ═══════════════════════════════════════════════════════════
class JarvisUI:
    # Cores base
    BG     = "#020a14"
    PANEL  = "#040e1c"
    PANEL2 = "#060f1e"
    AC     = "#00ccff"
    AC2    = "#003d52"
    AC3    = "#001e2a"
    TX     = "#7ac8e0"
    DIM    = "#1a3040"
    DIM2   = "#0d1e2e"
    GREEN  = "#00e87a"
    RED    = "#ff2244"
    YELLOW = "#ffcc00"
    ORANGE = "#ff8800"
    PURPLE = "#aa44ff"
    CYAN2  = "#00ffee"
    TEAL   = "#00bbaa"

    # Fontes
    F  = ("Consolas", 10)
    FT = ("Consolas", 20, "bold")
    FS = ("Consolas", 8)
    FB = ("Consolas", 9, "bold")

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
        self.root.title("J.A.R.V.I.S  —  Gesture Master HUD v5.2")
        self.root.geometry("1480x900")
        self.root.resizable(True, True)
        self.root.configure(bg=self.BG)
        self.root.minsize(1100, 700)

        self.menu_idx   = 0
        self._cam_on    = False
        self._ge        = GestureEngine()
        self.controller = GestureController(self)

        self._build()
        self._clock_tick()
        self._stats_tick()
        self._hud_pulse_tick()

        threading.Thread(target=listen_loop, args=(self,), daemon=True).start()

    # ════════════════════════════════════════════════════
    def _build(self):
        self._build_header()
        self._build_modebar()
        self._build_body()
        self._build_statusbar()

    # ── HEADER com arco decorativo ───────────────────────
    def _build_header(self):
        h = tk.Frame(self.root, bg=self.BG)
        h.pack(fill="x", padx=0, pady=0)

        # Canvas decorativo no header
        hc = tk.Canvas(h, height=64, bg=self.BG, highlightthickness=0)
        hc.pack(fill="x")

        # Linha de separação com gradiente manual
        def _draw_header(event=None):
            hc.delete("all")
            W = hc.winfo_width() or 1480

            # Linha principal
            for x in range(0, W, 2):
                t = x / W
                intensity = math.sin(math.pi * t) ** 2
                b = int(40 + intensity * 160)
                col = f"#00{b//2:02x}{b:02x}"
                hc.create_line(x, 62, x+2, 62, fill=col, width=1)

            # Aro de brilho superior
            for x in range(0, W, 4):
                t = x / W
                intensity = math.sin(math.pi * t) ** 3
                b = int(intensity * 80)
                if b > 5:
                    col = f"#00{b:02x}{min(255,b*2):02x}"
                    hc.create_line(x, 60, x+4, 60, fill=col, width=1)

            # Texto principal
            hc.create_text(14, 32, anchor="w",
                           text="J.A.R.V.I.S",
                           fill=self.AC, font=("Consolas", 26, "bold"))
            hc.create_text(190, 38, anchor="w",
                           text="Gesture Master HUD v5.2",
                           fill=self.DIM, font=("Consolas", 9))

            # Relógio
            now = datetime.datetime.now()
            hc.create_text(W-14, 22, anchor="e",
                           text=now.strftime("%H:%M:%S"),
                           fill=self.AC, font=("Consolas", 22, "bold"),
                           tags="clock")
            hc.create_text(W-14, 48, anchor="e",
                           text=now.strftime("%d/%m/%Y  %A"),
                           fill=self.DIM, font=("Consolas", 8),
                           tags="date")

            # Ornamento circular pequeno ao lado do título
            cx, cy = 155, 32
            for r in [18, 14, 10]:
                hc.create_oval(cx-r, cy-r, cx+r, cy+r,
                               fill="", outline=self.AC2, width=1)
            hc.create_oval(cx-5, cy-5, cx+5, cy+5, fill=self.AC, outline="")

        self._header_canvas = hc
        hc.bind("<Configure>", _draw_header)
        self._draw_header_fn = _draw_header

    def _refresh_header_clock(self):
        try:
            hc = self._header_canvas
            hc.delete("clock"); hc.delete("date")
            W = hc.winfo_width() or 1480
            now = datetime.datetime.now()
            hc.create_text(W-14, 22, anchor="e",
                           text=now.strftime("%H:%M:%S"),
                           fill=self.AC, font=("Consolas", 22, "bold"),
                           tags="clock")
            hc.create_text(W-14, 48, anchor="e",
                           text=now.strftime("%d/%m/%Y  %A"),
                           fill=self.DIM, font=("Consolas", 8),
                           tags="date")
        except: pass

    # ── BARRA MODOS ─────────────────────────────────────
    def _build_modebar(self):
        mb = tk.Frame(self.root, bg=self.BG, pady=3)
        mb.pack(fill="x", padx=10)

        # Separador esquerdo decorativo
        sep_left = tk.Canvas(mb, width=6, height=24, bg=self.BG, highlightthickness=0)
        sep_left.pack(side="left", padx=(4,6))
        sep_left.create_line(3, 0, 3, 24, fill=self.AC, width=2)

        tk.Label(mb, text="MODO:", fg=self.DIM, bg=self.BG,
                 font=("Consolas", 8)).pack(side="left", padx=(0,6))

        mode_def = {
            "CURSOR": (self.AC,    "↖"),
            "HOTKEY": (self.YELLOW,"⌨"),
            "VOLUME": (self.GREEN, "🔊"),
            "JARVIS": (self.PURPLE,"◈"),
        }
        self._mode_frames = {}
        for m, (color, icon) in mode_def.items():
            f = tk.Frame(mb, bg=self.DIM2, relief="flat")
            f.pack(side="left", padx=3)
            # Borda circular via Canvas
            c = tk.Canvas(f, width=80, height=26, bg=self.DIM2, highlightthickness=0)
            c.pack()
            c.create_rectangle(0, 0, 80, 26, fill=self.PANEL, outline=self.DIM, width=1)
            lbl_id = c.create_text(40, 13, text=f"{icon} {m}",
                                   fill=self.DIM, font=("Consolas", 8, "bold"))
            c.bind("<Button-1>", lambda e, mo=m: self.controller.set_mode(mo))
            c.bind("<Enter>",    lambda e, cv=c, li=lbl_id, cl=color: cv.itemconfig(li, fill=cl))
            c.bind("<Leave>",    lambda e, cv=c, li=lbl_id, mo=m:
                   cv.itemconfig(li, fill=self.AC if mo==self.controller.mode else self.DIM))
            self._mode_frames[m] = (f, c, lbl_id, color, icon)

        # Indicador de gesto — arredondado
        self._gesto_var = tk.StringVar(value="◈ —")
        gf = tk.Frame(mb, bg=self.AC2, relief="flat")
        gf.pack(side="right", padx=10)
        tk.Label(gf, textvariable=self._gesto_var, fg=self.AC,
                 bg=self.AC2, font=("Consolas", 10, "bold"),
                 padx=8, pady=2).pack()

        # VOZ status
        self._voice_var = tk.StringVar(value="🎙 en-GB-RyanNeural")
        tk.Label(mb, textvariable=self._voice_var, fg=self.GREEN,
                 bg=self.BG, font=("Consolas", 8)).pack(side="right", padx=8)

        # Volume bar
        self.vol_var = tk.IntVar(value=50)
        vf = tk.Frame(mb, bg=self.BG)
        vf.pack(side="right", padx=8)
        tk.Label(vf, text="VOL", fg=self.DIM, bg=self.BG,
                 font=self.FS).pack(side="left")
        ttk.Progressbar(vf, variable=self.vol_var, maximum=100,
                        length=70, mode='determinate').pack(side="left", padx=4)

        self.highlight_mode("CURSOR")

        # Linha de separação decorativa
        sep = tk.Canvas(self.root, height=2, bg=self.BG, highlightthickness=0)
        sep.pack(fill="x", padx=0)
        def _draw_sep(event=None):
            W = sep.winfo_width() or 1480
            sep.delete("all")
            for x in range(0, W, 2):
                t = x / W
                intensity = math.sin(math.pi * t) ** 2
                b = int(20 + intensity * 100)
                col = f"#00{b//3:02x}{b:02x}"
                sep.create_line(x, 1, x+2, 1, fill=col, width=1)
        sep.bind("<Configure>", _draw_sep)
        self._sep_canvas = sep

    # ── CORPO PRINCIPAL ──────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=2)
        body.columnconfigure(2, weight=3)
        body.rowconfigure(0, weight=1)
        self._build_cam_panel(body)
        self._build_log_panel(body)
        self._build_shortcuts_panel(body)

    # ── CÂMERA — painel circular ─────────────────────────
    def _build_cam_panel(self, parent):
        col = tk.Frame(parent, bg=self.BG)
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        col.rowconfigure(0, weight=3)
        col.rowconfigure(1, weight=1)
        col.rowconfigure(2, weight=1)
        col.columnconfigure(0, weight=1)

        # ─ Câmera circular ─
        cf = tk.Frame(col, bg=self.PANEL)
        cf.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        self._style_panel_round(cf)

        # Header do painel
        cam_hdr = tk.Frame(cf, bg=self.PANEL)
        cam_hdr.pack(fill="x", padx=10, pady=(8, 4))

        # Ornamento circular no header
        hdrc = tk.Canvas(cam_hdr, width=16, height=16,
                         bg=self.PANEL, highlightthickness=0)
        hdrc.pack(side="left", padx=(0, 6))
        hdrc.create_oval(2, 2, 14, 14, fill=self.AC2, outline=self.AC, width=1)
        hdrc.create_oval(5, 5, 11, 11, fill=self.AC, outline="")

        tk.Label(cam_hdr, text="CÂMERA  /  GESTURE ENGINE",
                 fg=self.AC, bg=self.PANEL, font=self.FB).pack(side="left")

        self._cam_st = tk.StringVar(value="● OFF")
        self._cam_st_lbl = tk.Label(cam_hdr, textvariable=self._cam_st,
                                     fg=self.RED, bg=self.PANEL, font=self.FS)
        self._cam_st_lbl.pack(side="right")

        # Arc Reactor canvas (substitui label da câmera)
        self._arc_canvas = JarvisArcCanvas(cf, size=268)
        self._arc_canvas.pack(padx=10, pady=4)

        # Controles
        ctrl = tk.Frame(cf, bg=self.PANEL)
        ctrl.pack(fill="x", padx=10, pady=(0, 8))

        self._cam_btn = tk.Button(
            ctrl, text=" ▶  ATIVAR ",
            bg=self.AC2, fg=self.AC, font=self.FB, relief="flat",
            cursor="hand2", activebackground=self.AC, activeforeground=self.BG,
            command=self._toggle_cam)
        self._cam_btn.pack(side="left", ipady=4, padx=(0, 8))

        tk.Label(ctrl, text="Smooth:", fg=self.DIM,
                 bg=self.PANEL, font=self.FS).pack(side="left", padx=(0, 2))
        self._sm_var = tk.DoubleVar(value=0.30)
        tk.Scale(ctrl, from_=0.05, to=1.0, resolution=0.05,
                 variable=self._sm_var, orient="horizontal", length=80,
                 bg=self.PANEL, fg=self.AC, troughcolor=self.DIM,
                 highlightthickness=0, showvalue=False,
                 command=lambda v: setattr(self.controller, '_SMTH', float(v))
                 ).pack(side="left")

        # ─ Referência rápida circular ─
        leg = tk.Frame(col, bg=self.PANEL)
        leg.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        self._style_panel_round(leg)

        leg_hdr = tk.Frame(leg, bg=self.PANEL)
        leg_hdr.pack(fill="x", padx=10, pady=(6, 2))
        self._mini_orb(leg_hdr)
        tk.Label(leg_hdr, text="REFERÊNCIA DE GESTOS",
                 fg=self.AC, bg=self.PANEL, font=self.FB).pack(side="left", padx=4)

        ref_data = [
            ("CURSOR", self.AC, [
                ("1 dedo","mover cursor"),("✌ 2 dedos","scroll"),
                ("punho+mv","arrastar janela"),("pinça","clique"),
                ("palma 0.7s","clique direito")]),
            ("HOTKEY", self.YELLOW, [
                ("1 dedo","Alt+Tab"),("2 dedos","Win+D"),
                ("3 dedos","Win+Tab"),("4 dedos","screenshot"),
                ("punho","Alt+F4"),("palma","snap janela")]),
            ("VOLUME", self.GREEN, [
                ("2 mãos dist","volume"),("1 dedo dir","vol +"),("punho dir","mute")]),
            ("JARVIS", self.PURPLE, [
                ("1↑","subir"),("2↓","descer"),("3","confirmar"),("palma","reset")]),
            ("TROCA", self.ORANGE, [
                ("esq 1","CURSOR"),("esq 2","HOTKEY"),("esq 3","VOLUME"),("esq palma","JARVIS")]),
        ]
        ref_txt = tk.Text(leg, bg=self.PANEL, fg=self.TX,
                          font=("Consolas", 7), relief="flat", wrap="word")
        ref_txt.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        ref_txt.tag_config("g", foreground=self.ORANGE)
        ref_txt.tag_config("a", foreground=self.GREEN)
        for mname, col_m, items in ref_data:
            ref_txt.insert("end", f"[{mname}]\n")
            ref_txt.tag_add(mname, ref_txt.index("end-2l"), ref_txt.index("end-1l"))
            ref_txt.tag_config(mname, foreground=col_m, font=("Consolas", 8, "bold"))
            for g, a in items:
                ref_txt.insert("end", f"  {g} ", "g")
                ref_txt.insert("end", f"→ {a}\n", "a")
        ref_txt.config(state="disabled")

        # ─ Menu Gestual ─
        mf = tk.Frame(col, bg=self.PANEL)
        mf.grid(row=2, column=0, sticky="nsew")
        self._style_panel_round(mf)

        mf_hdr = tk.Frame(mf, bg=self.PANEL)
        mf_hdr.pack(fill="x", padx=10, pady=(6, 2))
        self._mini_orb(mf_hdr)
        tk.Label(mf_hdr, text="MENU GESTUAL",
                 fg=self.AC, bg=self.PANEL, font=self.FB).pack(side="left", padx=4)
        tk.Label(mf, text="1↑  2↓  3=OK  palma=reset",
                 fg=self.DIM, bg=self.PANEL, font=("Consolas", 7)).pack(anchor="w", padx=10)

        mf2 = tk.Frame(mf, bg=self.PANEL)
        mf2.pack(fill="both", expand=True, padx=8, pady=(2, 6))
        self._menu_btns = []
        COLS = 2
        for idx, (label, mc) in enumerate(self.MENU_ITEMS):
            r2, c2 = divmod(idx, COLS)
            btn = tk.Button(mf2, text=label, bg=self.PANEL, fg=self.TX,
                            font=("Consolas", 8), relief="flat", cursor="hand2",
                            activebackground=self.AC2, activeforeground=self.AC,
                            anchor="w", command=lambda x=mc: self._run(x))
            btn.grid(row=r2, column=c2, padx=2, pady=1, sticky="ew")
            mf2.columnconfigure(c2, weight=1)
            self._menu_btns.append(btn)
        self.refresh_menu()

    # ── LOG ──────────────────────────────────────────────
    def _build_log_panel(self, parent):
        col = tk.Frame(parent, bg=self.BG)
        col.grid(row=0, column=1, sticky="nsew", padx=(0, 6))
        col.rowconfigure(0, weight=1)
        col.columnconfigure(0, weight=1)

        lf = tk.Frame(col, bg=self.PANEL)
        lf.grid(row=0, column=0, sticky="nsew")
        self._style_panel_round(lf)

        hdr = tk.Frame(lf, bg=self.PANEL)
        hdr.pack(fill="x", padx=10, pady=(8, 2))
        self._mini_orb(hdr)
        tk.Label(hdr, text="LOG DE COMUNICAÇÕES",
                 fg=self.AC, bg=self.PANEL, font=self.FB).pack(side="left", padx=4)
        tk.Button(hdr, text="limpar", bg=self.PANEL, fg=self.DIM,
                  font=self.FS, relief="flat", cursor="hand2",
                  command=lambda: (self.log.config(state="normal"),
                                   self.log.delete("1.0", "end"),
                                   self.log.config(state="disabled"))
                  ).pack(side="right")

        # Decoração circular ao lado do log
        log_deco = tk.Canvas(lf, height=3, bg=self.PANEL, highlightthickness=0)
        log_deco.pack(fill="x", padx=10)

        def _draw_logdeco(event=None):
            log_deco.delete("all")
            W = log_deco.winfo_width() or 400
            for x in range(0, W, 3):
                t = x / W
                b = int(20 + math.sin(math.pi * t) ** 2 * 80)
                col = f"#00{b//3:02x}{b:02x}"
                log_deco.create_line(x, 1, x+3, 1, fill=col, width=1)
        log_deco.bind("<Configure>", _draw_logdeco)

        self.log = tk.Text(lf, bg=self.PANEL, fg=self.TX,
                           font=("Consolas", 10),
                           insertbackground=self.AC, relief="flat",
                           wrap="word", selectbackground=self.AC2)
        self.log.pack(fill="both", expand=True, padx=8, pady=(2, 4))

        for tag, color in [("jarvis", self.AC), ("user", self.GREEN),
                            ("gesto", self.ORANGE), ("alerta", self.YELLOW),
                            ("erro", self.RED), ("info", self.DIM)]:
            self.log.tag_config(tag, foreground=color)
        self.log.config(state="disabled")

        # Input area
        inp_frame = tk.Frame(lf, bg=self.AC2, pady=1)
        inp_frame.pack(fill="x", padx=8, pady=(0, 8))

        inp = tk.Frame(inp_frame, bg=self.PANEL)
        inp.pack(fill="x", padx=1, pady=1)

        tk.Label(inp, text="›", fg=self.AC, bg=self.PANEL,
                 font=("Consolas", 14, "bold")).pack(side="left", padx=(6, 4))
        self.entry = tk.Entry(inp, bg=self.AC3, fg=self.AC,
                              insertbackground=self.AC,
                              font=("Consolas", 10), relief="flat",
                              highlightbackground=self.AC2, highlightthickness=1)
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", self._send)

        tk.Button(inp, text="SEND", bg=self.AC2, fg=self.AC,
                  font=self.FB, relief="flat", cursor="hand2",
                  padx=10, activebackground=self.AC, activeforeground=self.BG,
                  command=self._send).pack(side="left", padx=(4, 4), ipady=4)

    # ── PAINEL ATALHOS ───────────────────────────────────
    def _build_shortcuts_panel(self, parent):
        outer = tk.Frame(parent, bg=self.BG)
        outer.grid(row=0, column=2, sticky="nsew")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        cv = tk.Canvas(outer, bg=self.BG, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview,
                          bg=self.BG, troughcolor=self.DIM2)
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(cv, bg=self.BG)
        cw = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(cw, width=e.width))
        cv.bind_all("<MouseWheel>",
                    lambda e: cv.yview_scroll(int(-1*(e.delta/120)), "units"))

        # ─ Painel VOZ JARVIS circular ─
        vp = tk.Frame(inner, bg=self.PANEL)
        vp.pack(fill="x", pady=(0, 5))
        self._style_panel_round(vp, border_color=self.PURPLE)

        vhdr = tk.Frame(vp, bg=self.PANEL)
        vhdr.pack(fill="x", padx=10, pady=(8, 4))
        # Orbe roxo
        orbc = tk.Canvas(vhdr, width=16, height=16, bg=self.PANEL, highlightthickness=0)
        orbc.pack(side="left", padx=(0, 6))
        orbc.create_oval(2, 2, 14, 14, fill="#330055", outline=self.PURPLE, width=1)
        orbc.create_oval(5, 5, 11, 11, fill=self.PURPLE, outline="")
        tk.Label(vhdr, text="VOZ JARVIS", fg=self.PURPLE,
                 bg=self.PANEL, font=self.FB).pack(side="left")

        voice_info = [
            ("Motor:",  "Microsoft Edge Neural TTS"),
            ("Voz:",    "en-GB-RyanNeural"),
            ("Estilo:", "Britânico formal — JARVIS"),
            ("Pitch:",  f"{JARVIS_PITCH}  Rate: {JARVIS_RATE}"),
            ("Wake:",   "Diga 'JARVIS' para ativar"),
            ("Cache:",  f"{len(PRECACHE_PHRASES)} frases pré-geradas"),
        ]
        vp_inner = tk.Frame(vp, bg=self.PANEL)
        vp_inner.pack(fill="x", padx=12, pady=(0, 4))
        for lbl, val in voice_info:
            row = tk.Frame(vp_inner, bg=self.PANEL)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=lbl, fg=self.DIM, bg=self.PANEL,
                     font=("Consolas", 7), width=8, anchor="w").pack(side="left")
            tk.Label(row, text=val, fg=self.PURPLE, bg=self.PANEL,
                     font=("Consolas", 7), anchor="w").pack(side="left")

        tk.Button(vp, text="▶  TESTAR VOZ JARVIS",
                  bg=self.DIM2, fg=self.PURPLE, font=("Consolas", 8, "bold"),
                  relief="flat", cursor="hand2",
                  activebackground=self.PURPLE, activeforeground=self.BG,
                  command=lambda: threading.Thread(
                      target=speak,
                      args=("All systems are operational, sir. JARVIS online.", self),
                      daemon=True).start()
                  ).pack(fill="x", padx=10, pady=(0, 8))

        # ─ Status circular ─
        sf = tk.Frame(inner, bg=self.PANEL)
        sf.pack(fill="x", pady=(0, 5))
        self._style_panel_round(sf)

        sf_hdr = tk.Frame(sf, bg=self.PANEL)
        sf_hdr.pack(fill="x", padx=10, pady=(8, 4))
        self._mini_orb(sf_hdr)
        tk.Label(sf_hdr, text="STATUS DO SISTEMA",
                 fg=self.AC, bg=self.PANEL, font=self.FB).pack(side="left", padx=4)

        self.stat_vars = {}
        sg = tk.Frame(sf, bg=self.PANEL)
        sg.pack(fill="x", padx=10, pady=(0, 8))

        stat_items = [("CPU","cpu"),("RAM","ram"),("DISCO","disk"),("BAT","bat"),("IP","ip")]
        for i, (lbl, key) in enumerate(stat_items):
            r2, c2 = divmod(i, 2)
            # Frame com borda redonda simulada
            f2 = tk.Frame(sg, bg=self.DIM2, relief="flat")
            f2.grid(row=r2, column=c2, padx=3, pady=3, sticky="ew")
            sg.columnconfigure(c2, weight=1)

            # Mini indicador circular
            ic = tk.Canvas(f2, width=8, height=8, bg=self.DIM2, highlightthickness=0)
            ic.pack(side="left", padx=(4, 2), pady=4)
            ic.create_oval(1, 1, 7, 7, fill=self.AC, outline="")

            vf = tk.Frame(f2, bg=self.DIM2)
            vf.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)
            tk.Label(vf, text=lbl, fg=self.DIM, bg=self.DIM2,
                     font=("Consolas", 7)).pack(anchor="w")
            var = tk.StringVar(value="…")
            tk.Label(vf, textvariable=var, fg=self.AC, bg=self.DIM2,
                     font=("Consolas", 9, "bold")).pack(anchor="w")
            self.stat_vars[key] = var

        # ─ Calculadora ─
        CalcWidget(inner).pack(fill="x", pady=(0, 5))

        # ─ Atalhos por categoria ─
        for cat, items in self.ATALHOS.items():
            self._build_category(inner, cat, items)

    def _build_category(self, parent, cat_name, items):
        sec = tk.Frame(parent, bg=self.PANEL)
        sec.pack(fill="x", pady=(0, 5))
        self._style_panel_round(sec)

        hdr = tk.Frame(sec, bg=self.AC2, cursor="hand2")
        hdr.pack(fill="x")
        lbl = tk.Label(hdr, text=cat_name, fg=self.AC, bg=self.AC2,
                       font=self.FB)
        lbl.pack(side="left", padx=8, pady=4)
        arr = tk.Label(hdr, text="▲", fg=self.DIM, bg=self.AC2,
                       font=("Consolas", 8))
        arr.pack(side="right", padx=8)

        gf = tk.Frame(sec, bg=self.PANEL)
        gf.pack(fill="x", padx=6, pady=4)
        expanded = [True]
        COLS = 3

        for idx, (name, action, color) in enumerate(items):
            r2, c2 = divmod(idx, COLS)
            fn = action if callable(action) else lambda a=action: self._run(a)
            btn = tk.Button(gf, text=name, bg=self.DIM2, fg=self.TX,
                            font=("Consolas", 8), relief="flat", cursor="hand2",
                            anchor="w", pady=3,
                            activebackground=color, activeforeground="#ffffff",
                            command=fn)
            btn.grid(row=r2, column=c2, padx=2, pady=2, sticky="ew")
            gf.columnconfigure(c2, weight=1)
            btn.bind("<Enter>", lambda e, b=btn, cl=color: b.config(bg=cl, fg="#ffffff"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.DIM2, fg=self.TX))

        def toggle(_=None):
            if expanded[0]:
                gf.pack_forget(); arr.config(text="▼"); expanded[0] = False
            else:
                gf.pack(fill="x", padx=6, pady=4); arr.config(text="▲"); expanded[0] = True
        for w in (hdr, lbl, arr):
            w.bind("<Button-1>", toggle)

    # ── STATUS BAR ───────────────────────────────────────
    def _build_statusbar(self):
        # Separador
        sep = tk.Canvas(self.root, height=2, bg=self.BG, highlightthickness=0)
        sep.pack(fill="x")
        def _draw(event=None):
            W = sep.winfo_width() or 1480
            sep.delete("all")
            for x in range(0, W, 2):
                t = x / W
                b = int(15 + math.sin(math.pi*t)**2 * 70)
                sep.create_line(x, 1, x+2, 1, fill=f"#00{b//3:02x}{b:02x}", width=1)
        sep.bind("<Configure>", _draw)

        sb = tk.Frame(self.root, bg=self.BG)
        sb.pack(fill="x", padx=10, pady=(2, 4))

        # Orbe de status
        status_orb = tk.Canvas(sb, width=10, height=10,
                                bg=self.BG, highlightthickness=0)
        status_orb.pack(side="left", padx=(0, 6))
        status_orb.create_oval(1, 1, 9, 9, fill=self.GREEN, outline="")
        self._status_orb = status_orb

        self._status_var = tk.StringVar(value="SISTEMA ONLINE  |  CÂMERA INATIVA")
        tk.Label(sb, textvariable=self._status_var,
                 fg=self.GREEN, bg=self.BG, font=("Consolas", 8)).pack(side="left")

        # Teclas rápidas
        quick_kb = [
            ("Alt+Tab", lambda: AG_OK and pyautogui.hotkey('alt', 'tab')),
            ("Win+D",   lambda: AG_OK and pyautogui.hotkey('win', 'd')),
            ("Win+L",   lambda: ctypes.windll.user32.LockWorkStation()),
            ("Vol+",    lambda: vol_ctrl('up')),
            ("Vol-",    lambda: vol_ctrl('dn')),
            ("Mute",    lambda: vol_ctrl('mu')),
            ("Print",   lambda: AG_OK and pyautogui.press('printscreen')),
        ]
        for label, fn in quick_kb:
            b = tk.Button(sb, text=label, bg=self.DIM2, fg=self.DIM,
                          font=("Consolas", 7), relief="flat", cursor="hand2",
                          padx=6, activebackground=self.AC2, activeforeground=self.AC,
                          command=lambda f=fn: threading.Thread(target=f, daemon=True).start())
            b.pack(side="right", padx=2, ipady=3)
            b.bind("<Enter>", lambda e, btn=b: btn.config(fg=self.AC, bg=self.AC3))
            b.bind("<Leave>", lambda e, btn=b: btn.config(fg=self.DIM, bg=self.DIM2))

    # ════════════════════════════════════════════════════
    # UTILIDADES VISUAIS
    # ════════════════════════════════════════════════════
    def _style_panel_round(self, frame, border_color=None):
        """Simula borda arredondada via highlightthickness."""
        col = border_color or self.AC2
        frame.config(highlightbackground=col, highlightthickness=1)

    def _mini_orb(self, parent):
        """Pequeno orbe circular decorativo."""
        c = tk.Canvas(parent, width=14, height=14,
                      bg=self.PANEL, highlightthickness=0)
        c.pack(side="left")
        c.create_oval(2, 2, 12, 12, fill=self.AC2, outline=self.AC, width=1)
        c.create_oval(5, 5, 9, 9, fill=self.AC, outline="")

    def _hud_pulse_tick(self):
        """Pulsa o orbe de status."""
        try:
            t = time.time()
            pulse = (math.sin(t * 2) + 1) / 2
            b = int(160 + pulse * 95)
            col = f"#00{b:02x}7a"
            self._status_orb.delete("all")
            self._status_orb.create_oval(1, 1, 9, 9, fill=col, outline="")
        except: pass
        self.root.after(100, self._hud_pulse_tick)

    # ════════════════════════════════════════════════════
    # CÂMERA LOOP
    # ════════════════════════════════════════════════════
    def _toggle_cam(self):
        if not CV2_OK:
            self.add_log("⚠ mediapipe/opencv não instalados!", "erro"); return
        if not self._cam_on: self._start_cam()
        else: self._stop_cam()

    def _start_cam(self):
        if not self._ge.start():
            self.add_log("⚠ Webcam não encontrada.", "erro"); return
        self._cam_on = True
        self._cam_btn.config(text=" ■  PARAR ", bg="#1a0008", fg=self.RED,
                              activebackground=self.RED, activeforeground=self.BG)
        self._cam_st.set("● ON")
        self._cam_st_lbl.config(fg=self.GREEN)
        self._status_var.set("CÂMERA ATIVA  —  RECONHECENDO GESTOS")
        self.add_log("✔ Câmera ativada.", "gesto")
        speak("Camera activated. Gesture control is now online, sir.", self)
        threading.Thread(target=self._cam_loop, daemon=True).start()

    def _stop_cam(self):
        self._cam_on = False
        self._ge.stop()
        self._cam_btn.config(text=" ▶  ATIVAR ", bg=self.AC2, fg=self.AC,
                              activebackground=self.AC, activeforeground=self.BG)
        self._cam_st.set("● OFF")
        self._cam_st_lbl.config(fg=self.RED)
        self._status_var.set("SISTEMA ONLINE  |  CÂMERA INATIVA")
        self._gesto_var.set("◈ —")
        # Volta ao arc reactor animado
        try:
            self._arc_canvas.clear_image()
            self._arc_canvas._active = True
        except: pass
        self.add_log("■ Câmera desligada.", "info")
        speak("Camera deactivated, sir.", self)

    def _cam_loop(self):
        while self._cam_on:
            frame, right, left, cr, cl = self._ge.read()
            if frame is None:
                time.sleep(0.04); continue
            parts = []
            if right: parts.append(f"DIR:{right['g']}")
            if left:  parts.append(f"ESQ:{left['g']}")
            self.root.after(0, lambda p=" | ".join(parts) if parts else "—":
                            self._gesto_var.set(f"◈ {p}"))
            self.controller.process(right, left, cr, cl)
            try:
                sm = cv2.resize(frame, (268, 268))
                sm_rgb = cv2.cvtColor(sm, cv2.COLOR_BGR2RGB)
                img = tk.PhotoImage(
                    data=cv2.imencode('.ppm', cv2.cvtColor(sm_rgb, cv2.COLOR_RGB2BGR))[1].tobytes())
                self.root.after(0, lambda i=img: self._upd_cam(i))
            except: pass
            time.sleep(0.025)

    def _upd_cam(self, img):
        try:
            self._arc_canvas.delete("all")
            self._arc_canvas.create_image(134, 134, image=img, anchor="center")
            self._arc_canvas._cam_img = img  # evita GC
        except: pass

    # ════════════════════════════════════════════════════
    # MENU GESTUAL
    # ════════════════════════════════════════════════════
    def refresh_menu(self):
        for i, btn in enumerate(self._menu_btns):
            if i == self.menu_idx:
                btn.config(bg=self.AC2, fg=self.AC,
                           font=("Consolas", 8, "bold"), relief="groove")
            else:
                btn.config(bg=self.PANEL, fg=self.TX,
                           font=("Consolas", 8), relief="flat")

    def menu_up(self):
        self.menu_idx = (self.menu_idx - 1) % len(self.MENU_ITEMS)
        self.refresh_menu()

    def menu_down(self):
        self.menu_idx = (self.menu_idx + 1) % len(self.MENU_ITEMS)
        self.refresh_menu()

    def menu_confirm(self):
        label, mc = self.MENU_ITEMS[self.menu_idx]
        self.add_log(f"GESTO CONFIRM › {label}", "gesto")
        self._run(mc)

    # ════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ════════════════════════════════════════════════════
    def highlight_mode(self, active):
        for m, (f, c, lbl_id, color, icon) in self._mode_frames.items():
            if m == active:
                c.config(bg=color)
                c.itemconfig(lbl_id, fill=self.BG)
                for child in f.winfo_children():
                    try: child.config(bg=color)
                    except: pass
            else:
                c.config(bg=self.PANEL)
                c.itemconfig(lbl_id, fill=self.DIM)
                for child in f.winfo_children():
                    try: child.config(bg=self.PANEL)
                    except: pass

    def update_stats(self, info):
        for k in ["cpu", "ram", "disk", "bat", "ip"]:
            if k in self.stat_vars and k in info:
                self.stat_vars[k].set(info[k])

    def add_log(self, text, tag=None):
        def _i():
            self.log.config(state="normal")
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.log.insert("end", f"[{ts}]  ", "info")
            self.log.insert("end", text + "\n", tag or "")
            self.log.see("end")
            self.log.config(state="disabled")
        self.root.after(0, _i)

    def _send(self, event=None):
        q = self.entry.get().strip()
        if not q: return
        self.entry.delete(0, "end")
        self.add_log(f"VOCÊ › {q}", "user")
        resp = jarvis_response(q)
        speak(resp, self)
        threading.Thread(target=cmd, args=(q, self), daemon=True).start()

    def _run(self, action):
        if callable(action):
            threading.Thread(target=action, daemon=True).start()
        else:
            self.add_log(f"CMD › {action}", "user")
            resp = jarvis_response(action)
            speak(resp, self)
            threading.Thread(target=cmd, args=(action, self), daemon=True).start()

    def _clock_tick(self):
        self._refresh_header_clock()
        self.root.after(1000, self._clock_tick)

    def _stats_tick(self):
        info = sys_info()
        self.update_stats(info)
        self.root.after(5000, self._stats_tick)

    # ════════════════════════════════════════════════════
    def run(self):
        self.add_log("⏳ Pré-gerando cache de voz JARVIS... aguarde.", "alerta")
        def _boot():
            _speak_ready.wait(timeout=15)
            speak("JARVIS Gesture Master online. All modules loaded. Ready for your command, sir.", self)
        threading.Thread(target=_boot, daemon=True).start()
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════
# ENTRY POINT — Arc Reactor Splash → HUD Principal
# ═══════════════════════════════════════════════════════════
def _launch_main():
    """Lança a interface principal após o splash."""
    ui = JarvisUI()
    ui.run()

if __name__ == "__main__":
    # Tela de abertura Arc Reactor, depois lança o HUD
    splash = ArcReactorSplash(on_complete=_launch_main)
    splash.run()