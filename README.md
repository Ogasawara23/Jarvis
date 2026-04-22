# Jarvis
🤖 J.A.R.V.I.S — Gesture Master HUD v5.1

Sistema avançado estilo JARVIS inspirado no universo do Homem de Ferro, com:

🎙️ Comandos de voz (PT-BR → resposta em inglês estilo JARVIS)
🖐️ Controle por gestos com webcam
🖥️ Interface HUD futurista
🔊 Voz neural realista (Microsoft Edge TTS)
⚡ Automação do sistema (volume, apps, atalhos, etc)
🚀 Tecnologias utilizadas
Python 3
OpenCV (visão computacional)
MediaPipe (detecção de mãos)
Tkinter (interface gráfica)
Edge TTS (voz neural)
PyAutoGUI (controle do sistema)
SpeechRecognition (voz)
Pycaw (controle de áudio Windows)
📦 Instalação completa (PowerShell)

Abra o PowerShell e execute:

pip install mediapipe opencv-python numpy pyautogui
pip install SpeechRecognition psutil pywin32 pycaw comtypes
pip install edge-tts pygame
📚 Explicação das bibliotecas
🖐️ Visão computacional
mediapipe → Detecta mãos e gestos
opencv-python → Captura e processa webcam
numpy → Cálculos matemáticos
🖱️ Automação do sistema
pyautogui → Controla mouse, teclado e ações do sistema
🎙️ Voz e áudio
SpeechRecognition → Reconhece comandos de voz
edge-tts → Gera voz estilo JARVIS (neural)
pygame → Reproduz áudio gerado
💻 Sistema
psutil → Informações do sistema (CPU, RAM, etc)
pywin32 → Integração com Windows
pycaw + comtypes → Controle de volume do sistema
⚙️ Requisitos
Python 3.10+
Windows (recomendado)
Webcam
Microfone
Internet (necessário para voz com edge-tts)
