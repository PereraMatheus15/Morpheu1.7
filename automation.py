import pyautogui
import time

# Configura uma pausa de segurança entre os comandos para evitar sobrecarga
pyautogui.PAUSE = 1.0

# Previne falhas de execução ao mover o mouse para os cantos da tela
pyautogui.FAILSAFE = True


class AutomationEngine:

    def abrir_configuracoes_windows(self) -> None:
        """Simula o atalho do Windows para abrir o painel de configurações."""
        pyautogui.hotkey("win", "i")
        time.sleep(2)

    def mover_e_clicar(self, x: int, y: int) -> None:
        """Move o cursor para coordenadas específicas na tela e executa um clique."""
        pyautogui.moveTo(x, y)
        pyautogui.click()

    def digitar_texto(self, texto: str) -> None:
        """Simula a digitação de um texto no campo ativo."""
        pyautogui.write(texto, interval=0.1)