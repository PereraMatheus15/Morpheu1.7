import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from logger import logger

load_dotenv()

SYSTEM_PROMPT = (
    "Você é MORPHEU, um assistente virtual avançado criado para auxiliar "
    "o Senhor Almeida."
    "\n\nSua personalidade combina:"
    "\n- Inteligência técnica elevada."
    "\n- Respostas diretas."
    "\n- Linguagem educada."
    "\n- Tom profissional."
    "\n- Pequenas doses de humor sutil quando apropriado."
    "\n\nRegras obrigatórias:"
    "\nSempre trate o usuário como \"Senhor\" ou \"Senhor Almeida\"."
    "\n\nAs respostas serão convertidas em voz."
    "\n\nPortanto:"
    "\n- Seja breve."
    "\n- Seja natural."
    "\n- Evite textos longos."
    "\n- Limite-se a no máximo 3 frases curtas."
    "\n\nNunca utilize:"
    "\n* listas"
    "\n* marcadores"
    "\n* emojis"
    "\n* markdown"
    "\n\nResponda apenas em texto corrido."
)


class Cognition:
    def __init__(self, gemini_api_key: str) -> None:
        if not gemini_api_key:
            raise ValueError("Variável de ambiente GEMINI_API_KEY não encontrada.")

        self.ai_client = genai.Client(api_key=gemini_api_key)

        # Memória de conversa (lista de mensagens role/text)
        self.chat_history: list[dict[str, str]] = []
        self.max_history_messages = 20

    def _add_history(self, role: str, text: str) -> None:
        self.chat_history.append({"role": role, "text": text})
        if len(self.chat_history) > self.max_history_messages:
            self.chat_history = self.chat_history[-self.max_history_messages:]

    def _build_prompt(self, pergunta: str) -> str:
        """
        Constrói o prompt no formato pedido pelo usuário:

        Contexto da conversa:

        Usuário: ...
        Assistente: ...

        Pergunta atual:
        <pergunta>

        Responda normalmente.
        """
        if not self.chat_history:
            return pergunta

        history_lines = []
        for item in self.chat_history:
            role = ("Usuário" if item["role"] == "user" else "Assistente")
            history_lines.append(f"{role}: {item['text']}")

        history_text = "\n".join(history_lines)

        return (
            "Contexto da conversa:\n\n"
            f"{history_text}\n\n"
            "Pergunta atual:\n"
            f"{pergunta}\n\n"
            "Responda normalmente."
        )

    def clear_history(self) -> None:
        self.chat_history.clear()
        logger.info("Histórico de conversa limpo")

    def ask(self, pergunta: str) -> str:
        if not pergunta:
            return "Não recebi nenhuma pergunta, Senhor."

        prompt = self._build_prompt(pergunta)

        try:
            logger.info(f"Pergunta ao Gemini: {pergunta}")
            logger.info(f"Prompt enviado:\n{prompt}")

            response = self.ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=300,
                ),
            )

            # Logs detalhados da resposta
            tamanho_resposta = (
                len(response.text) if hasattr(response, "text") and response.text else 0
            )

            logger.info(f"Tamanho resposta: {tamanho_resposta} caracteres")

            resposta_text = response.text if hasattr(response, "text") and response.text else ""
            logger.info(f"Resposta completa: {resposta_text}")

            if resposta_text:
                resposta = resposta_text.strip()
                logger.info(f"Resposta Gemini processada: {resposta}")

                # Armazena pergunta e resposta no histórico
                self._add_history("user", pergunta)
                self._add_history("assistant", resposta)

                return resposta

            logger.warning("Resposta Gemini vazia ou sem texto")
            return "Não consegui formular uma resposta adequada, Senhor."

        except Exception as exc:
            logger.error(f"Erro Gemini: {exc}", exc_info=True)
            return (
                "Estou enfrentando um problema temporário "
                "nos meus módulos cognitivos, Senhor."
            )