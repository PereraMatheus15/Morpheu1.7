import os
import queue
import subprocess
import sys
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

ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

WAKE_WORD = "morpheu"
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
    if not ELEVEN_API_KEY or not GEMINI_API_KEY:
        logger.error("Erro: as variáveis de ambiente ELEVEN_API_KEY e GEMINI_API_KEY devem estar definidas.")
        sys.exit(1)

    command_queue: queue.Queue[dict[str, str]] = queue.Queue()
    cognition = Cognition(GEMINI_API_KEY)
    audio_engine = AudioEngine()
    listener = Listener(command_queue, wake_word=WAKE_WORD, energy_threshold=250)
    
    # Inicializa o mecanismo de automação integrado
    automation = AutomationEngine()

    # audio_engine.start()
    listener.start()

    logger.info("Sistema iniciado")
    audio_engine.enqueue_text(
        "Sistemas online, Senhor Almeida. Estou pronto para receber comandos."
    )

    try:
        while True:
            logger.info("Loop principal ativo")
            logger.info(f"Aguardando comando na fila (size={command_queue.qsize()})")
            
            try:
                # 1. Aguarda o comando chegar da fila (com timeout para não travar)
                item = command_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            logger.info(f"Comando recebido da fila: {item}")
            if item.get("type") != "wake":
                continue

            # 2. Extrai e limpa o comando bruto
            raw_command = item.get("text", "").lower()
            logger.info(f"Comando bruto: {raw_command}")
            
            # Corta a fala atual imediatamente ao ouvir o próprio nome
            audio_engine.interrupt()

            clean_command = raw_command.replace(WAKE_WORD, "").strip()
            
            # 3. Se ouviu apenas "Morpheu" e não disse mais nada
            if not clean_command:
                audio_engine.enqueue_text("Sim, Senhor Almeida? Estou ouvindo.")
                logger.info("Texto enviado ao AudioEngine: resposta vazia de wake word")
                continue

            # ==========================================
            # FLUXO DE DECISÃO UNIFICADO E HIERÁRQUICO
            # ==========================================
            
            # 1º Passo: Tenta executar no Windows (local_ops.py)
            resposta_local = executar_comando_local(clean_command)
            
            if resposta_local:
                logger.info(f"Ação local executada: {resposta_local}")
                audio_engine.enqueue_text(resposta_local)
                continue  # Pula para a próxima iteração
            
            # 2º Passo: Tenta os comandos estáticos (pesquisa web, hora exata, configurações)
            resultado_estatico = processar_comandos(clean_command, audio_engine, cognition, automation)
            
            if resultado_estatico is False:
                # Se a função retornar False propositalmente para desligar (ex: "encerrar sistema")
                logger.info("Comando de encerramento detectado")
                break
                
            if resultado_estatico is True:
                # O comando estático foi processado com sucesso
                logger.info("Comando estático processado")
                continue

            # 3º Passo: Se não for ação local nem comando estático, envia para a IA conversar
            logger.info("Enviando pergunta para Cognition")
            resposta = cognition.ask(clean_command)
            logger.info(f"Resposta recebida da Cognition: {resposta}")
            audio_engine.enqueue_text(resposta)
            logger.info("Texto enviado ao AudioEngine")

    except KeyboardInterrupt:
        logger.info("Encerrando por KeyboardInterrupt")
    finally:
        listener.stop()
        audio_engine.interrupt()
        # Certifique-se de que o método stop() existe no seu audio_engine ou remova a linha abaixo
        if hasattr(audio_engine, 'stop'):
            audio_engine.stop()
        listener.join(timeout=2.0)

if __name__ == "__main__":
    main()