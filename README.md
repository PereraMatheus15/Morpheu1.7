🌌 Morpheu - Assistente Pessoal Multimodal
Um assistente pessoal inteligente e de baixa latência, acionado por voz (usando wake word), projetado para rodar nativamente no Windows sem complicações de compilação. O projeto é integrado aos modelos mais recentes da Google e utiliza síntese de voz natural.

🚀 Funcionalidades Principais
🎧 Escuta Contínua e Wake Word: Fica em modo de espera aguardando a palavra "assistente". Após a ativação, aguarda um comando por voz e retorna ao modo de espera ao terminar.

⚡ Reconhecimento de Voz Local: Utiliza Faster-Whisper em CPU para transcrever português brasileiro localmente, sem enviar o áudio a uma API de reconhecimento.

🎙️ Captação de Áudio Nativa: Utiliza sounddevice e numpy para capturar áudio mono a 16 kHz diretamente do microfone.

🧠 Inteligência Multimodal Avançada: Processa os áudios e comandos utilizando o modelo Gemini 2.5 Flash da Google, garantindo respostas rápidas, contextuais e precisas.

🗣️ Voz Natural e Fluida: Usa Edge-TTS e, se o serviço estiver indisponível, tenta a síntese local do Windows (SAPI).

🛠️ Tecnologias e Bibliotecas Utilizadas
Linguagem: Python 3.13+ (validado neste ambiente com Python 3.14)

IA & Processamento: google-genai (Gemini API)

Áudio (Captação e Reconhecimento): sounddevice, numpy, Faster-Whisper

Voz (TTS): edge-tts, pygame (pygame-ce no Python 3.14+), Windows SAPI como fallback local

Gerenciamento de Eventos: Arquitetura modular e assíncrona

⚙️ Configuração e Execução
1. Requisitos e Instalação
Certifique-se de estar utilizando um ambiente virtual (.venv) e instale as dependências necessárias:

PowerShell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
2. Variáveis de Ambiente
O reconhecimento de voz é local depois do download inicial do modelo Faster-Whisper. Para perguntas encaminhadas à IA, configure uma chave válida do Gemini em `GEMINI_API_KEY` no ambiente ou no `.env` da raiz do projeto; valores de exemplo/placeholder são ignorados. A variável definida no ambiente tem precedência. Comandos locais e estáticos continuam disponíveis sem uma chave válida.

Defina a sua chave de API do Gemini no terminal antes de rodar o assistente:

No PowerShell:

PowerShell
$env:GEMINI_API_KEY="sua-api-key-aqui"
No Prompt de Comando (CMD):

DOS
set GEMINI_API_KEY=sua-api-key-aqui
3. Iniciando o Sistema
Execute o script principal:

PowerShell
.\.venv\Scripts\python.exe main.py

Para executar os testes simulados do Listener, sem usar o microfone:

PowerShell
.\.venv\Scripts\python.exe -m unittest -v test_listener test_local_ops test_cognition test_tts

Para testar a geração de "Estou ouvindo." pelo Edge-TTS (com fallback SAPI no Windows), sem reproduzir o áudio:

PowerShell
.\.venv\Scripts\python.exe tts_smoke_test.py
📌 Status do Projeto
Atualmente na versão 1.0 (v1.py), com o subsistema de escuta ativa e processamento multimodal reestruturados para máxima eficiência e compatibilidade.

Sinta-se à vontade para abrir issues ou enviar pull requests para contribuir com o projeto, Senhor.
