from typing import Optional

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
    def __init__(self, gemini_api_key: Optional[str]) -> None:
        key = (gemini_api_key or "").strip()
        if self._is_placeholder_key(key):
            key = ""

        self.ai_client = genai.Client(api_key=key) if key else None

        # Memória de conversa (lista de mensagens role/text)
        self.chat_history: list[dict[str, str]] = []
        self.max_history_messages = 20

    @staticmethod
    def _is_placeholder_key(key: str) -> bool:
        normalized = key.casefold()
        return any(
            marker in normalized
            for marker in ("your_", "placeholder", "replace", "example", "changeme")
        )

    @staticmethod
    def _is_authentication_error(exc: Exception) -> bool:
        details = str(exc).casefold()
        return any(
            marker in details
            for marker in (
                "api_key_invalid",
                "api key not valid",
                "invalid api key",
                "unauthenticated",
            )
        )

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

        if self.ai_client is None:
            logger.warning(
                "Gemini indisponível: configure uma chave válida em GEMINI_API_KEY."
            )
            return (
                "A inteligência Gemini está indisponível. "
                "Configure uma chave válida em GEMINI_API_KEY, Senhor."
            )

        prompt = self._build_prompt(pergunta)

        try:
            logger.info(f"Pergunta ao Gemini: {pergunta}")

            response = self.ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=1024,
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
            if self._is_authentication_error(exc):
                logger.error(
                    "Autenticação Gemini recusada; verifique GEMINI_API_KEY."
                )
                return (
                    "A chave de autenticação do Gemini foi recusada. "
                    "Verifique GEMINI_API_KEY, Senhor."
                )

            status_code = getattr(exc, "code", None)

            logger.error(
                    "Erro Gemini: tipo=%s, status=%s",
     type(exc).__name__,
            status_code,
)