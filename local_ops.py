import os
import subprocess

def executar_comando_local(comando: str) -> str:
    comando = comando.lower().strip()

    # Módulo de Abertura de Programas
    if comando.startswith("abrir ") or comando.startswith("iniciar "):
        alvo = comando.replace("abrir ", "").replace("iniciar ", "").strip()
        
        # Dicionário de atalhos para facilitar o reconhecimento
        atalhos = {
            "navegador": "chrome",
            "google": "chrome",
            "bloco de notas": "notepad",
            "calculadora": "calc",
            "editor": "code",  # Inicia o VS Code
            "terminal": "cmd"
        }

        # Busca no dicionário, se não achar, tenta o nome direto
        programa = atalhos.get(alvo, alvo)
        
        try:
            # O comando 'start' do Windows resolve os caminhos automaticamente
            os.system(f"start {programa}")
            return f"Iniciando {alvo} imediatamente, Senhor."
        except Exception as e:
            return f"Uh, encontrei dificuldades para localizar o executável do {alvo}."

    # Módulo de Sistema (Exemplos adicionais)
    if "limpar lixeira" in comando:
        try:
            os.system("rd /s /q %systemdrive%\\$Recycle.bin")
            return "Lixeira esvaziada com sucesso."
        except Exception:
            return "Não consegui acessar a lixeira, Senhor."

    # Retorna vazio se não for um comando local, passando a bola para a IA
    return ""