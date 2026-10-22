import os
import queue
import subprocess
import time
import webbrowser
from typing import Optional

from dotenv import load_dotenv
from audio_engine import AudioEngine
from cognition import Cognition
from listener import Listener
from logger import logger
from automation import AutomationEngine
from local_ops import executar_comando_local

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

WAKE_WORD = "assistente"
JARVIS_VOICE_ID = "gvLz73B6mpicDP3zbCkU"


def processar_comandos(comando: str, engine: AudioEngine, brain: Cognition, automation: AutomationEngine) -> Optional[bool]:
    comando = comando.lower().strip()

    if "configuração" in comando or "configurações" in comando:
        engine.enqueue_text("Abrindo as configurações do Windows, Senhor.")
        automation.abrir_configuracoes_windows()
        return True

    if "que horas são" in comando or "que horas" in comando:
        agora = time.strftime("%H:%M")
        comentario = (
            "A manhã está voando, Senhor."
            if time.localtime().tm_hour < 12
            else "O tempo continua avançando, Senhor."
        )
        engine.enqueue_text(f"São exatamente {agora}. {comentario}")
        return True

    if "pesquisar por" in comando:
        termo = comando.split("pesquisar por", 1)[1].strip()
        if termo:
            engine.enqueue_text(f"Pesquisando por {termo}, Senhor.")
            webbrowser.open(f"https://www.google.com/search?q={termo.replace(' ', '+')}")
        return True

    if "youtube" in comando:
        engine.enqueue_text("Abrindo o YouTube, Senhor.")
        webbrowser.open("https://youtube.com")
        return True

    if any(keyword in comando for keyword in ("codigo", "código", "desenvolvimento")):
        try:
            subprocess.Popen(["cmd", "/c", "code"], shell=True)
            engine.enqueue_text("Abrindo o Visual Studio Code, Senhor.")
        except Exception:
            engine.enqueue_text("Não consegui localizar o Visual Studio Code.")
        return True

    if any(keyword in comando for keyword in ("sair", "encerrar", "tchau")):
        engine.enqueue_text("Encerrando os sistemas. Até logo, Senhor.")
        return False

    return None


def main() -> None:
    command_queue: queue.Queue[dict[str, str]] = queue.Queue()
    cognition = Cognition(GEMINI_API_KEY)
    listener = Listener(command_queue, wake_word=WAKE_WORD, energy_threshold=400)
    audio_engine = AudioEngine()
    
    # Inicializa o mecanismo de automação integrado
    automation = AutomationEngine()

    try:
        logger.info("Sistema iniciado")
        audio_engine.enqueue_text(
            "Sistemas online, Senhor Almeida. Estou pronto para receber comandos."
        )
        audio_engine.queue.join()
        listener.start()
        logger.info("Aguardando palavra de ativação.")

        while True:
            try:
                item = command_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            should_exit = False
            try:
                logger.info(f"Evento recebido da fila: {item}")
                item_type = item.get("type")

                if item_type == "wake":
                    logger.info("Morpheu: Estou ouvindo.")
                    audio_engine.enqueue_text("Estou ouvindo.")
                    audio_engine.queue.join()
                    listener.resume_after_audio()
                    continue

                if item_type != "command":
                    continue

                clean_command = item.get("text", "").lower().strip()
                if not clean_command:
                    logger.warning("Comando vazio ignorado.")
                    listener.resume_after_audio()
                    continue

                logger.info(f"Comando reconhecido: {clean_command}")
                resposta_local = executar_comando_local(clean_command)

                if resposta_local:
                    logger.info(f"Ação local executada: {resposta_local}")
                    audio_engine.enqueue_text(resposta_local)
                else:
                    resultado_estatico = processar_comandos(
                        clean_command,
                        audio_engine,
                        cognition,
                        automation,
                    )

                    if resultado_estatico is False:
                        logger.info("Comando de encerramento detectado")
                        audio_engine.queue.join()
                        should_exit = True
                    elif resultado_estatico is None:
                        logger.info("Enviando pergunta para Cognition")
                        resposta = cognition.ask(clean_command)
                        logger.info(f"Resposta recebida da Cognition: {resposta}")
                        audio_engine.enqueue_text(resposta)

                if not should_exit:
                    audio_engine.queue.join()
                    listener.resume_after_audio()
            finally:
                command_queue.task_done()

            if should_exit:
                break

    except KeyboardInterrupt:
        logger.info("Encerrando por KeyboardInterrupt")

    finally:
        listener.stop()
        listener.join()
        audio_engine.shutdown()

if __name__ == "__main__":
    main()