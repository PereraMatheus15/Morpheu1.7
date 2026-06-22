import os
import time
import tempfile
import datetime
import webbrowser
import subprocess
import speech_recognition as sr
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from playsound import playsound
from imageio_ffmpeg import get_ffmpeg_exe
from pydub import AudioSegment

# Configuração do motor de conversão de áudio (FFMPEG)
AudioSegment.converter = get_ffmpeg_exe()

# ================= CONFIGURAÇÃO OPERACIONAL =================
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "your_eleven_api_key_here")
JARVIS_VOICE_ID = "gvLz73B6mpicDP3zbCkU"
WAKE_WORD = "jarvis"

# Configuração do Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
genai.configure(api_key=GEMINI_API_KEY)

ARQUIVO_AUDIO = os.path.join(tempfile.gettempdir(), "jarvis_final_response.mp3")
# ============================================================

eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT_SISTEMA = (
    "Você é o J.A.R.V.I.S., o assistente pessoal do Senhor Almeida. "
    "Sua personalidade é inteligente, profissional e irônica. "
    "Sempre se dirija a ele como 'Senhor' ou 'Senhor Almeida'. "
    "Seja extremamente conciso (máximo 3 frases). "
    "Inclua pausas orgânicas como 'Uh, vejamos...' ou 'Sim, Senhor...'. "
    "NUNCA use listas, tópicos ou asteriscos. Escreva apenas em prosa limpa."
)

def speak(texto: str) -> None:
    print(f"Jarvis: {texto}")
    try:
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=JARVIS_VOICE_ID,
            text=texto,
            model_id="eleven_multilingual_v2",
            optimize_streaming_latency="0"
        )
        with open(ARQUIVO_AUDIO, "wb") as f:
            for chunk in audio_stream:
                if chunk: f.write(chunk)
            f.flush()
            os.fsync(f.fileno())
        
        playsound(ARQUIVO_AUDIO)
        time.sleep(0.2)
        if os.path.exists(ARQUIVO_AUDIO):
            os.remove(ARQUIVO_AUDIO)
    except Exception as e:
        print(f"Falha no subsistema de voz: {e}")

def ask_gemini(pergunta: str) -> str:
    try:
        response = model.generate_content(
            f"{PROMPT_SISTEMA}\n\nUsuário: {pergunta}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"Erro na API Gemini: {e}")
        return "Uh, um breve contratempo nos meus servidores, Senhor."

def listen() -> str:
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 250
    recognizer.pause_threshold = 1.2
    
    try:
        with sr.Microphone() as source:
            print("\n[MONITORANDO AMBIENTE...]")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
    except Exception as exc:
        print(f"Erro de hardware: {exc}")
        return ""
        
    try:
        return recognizer.recognize_google(audio, language="pt-BR").lower()
    except:
        return ""

def handle_command(comando: str) -> bool:
    if any(x in comando for x in ["sair", "encerrar", "tchau"]):
        speak("Sim, Senhor... Desconectando.")
        return False
    elif "youtube" in comando:
        speak("Acessando o YouTube.")
        webbrowser.open("https://youtube.com")
    elif "horas" in comando:
        speak(f"São exatamente {datetime.datetime.now().strftime('%H:%M')}, Senhor.")
    else:
        print(f"[PROCESSANDO] {comando}")
        speak(ask_gemini(comando))
    return True

def main() -> None:
    speak("Sistemas online, Senhor Almeida.")
    while True:
        comando = listen()
        if WAKE_WORD in comando:
            comando_puro = comando.replace(WAKE_WORD, "").strip()
            if not handle_command(comando_puro):
                break
        time.sleep(0.4)

if __name__ == "__main__":
    main()