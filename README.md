🌌 Morpheu - Assistente Pessoal Multimodal

O Morpheu é um assistente pessoal inteligente acionado por voz, desenvolvido para Windows e projetado para operar com baixa latência, reconhecimento de fala local e respostas geradas por IA de última geração.

Seu objetivo é oferecer uma experiência fluida e natural, mantendo a privacidade do usuário ao realizar a transcrição de voz localmente e utilizando os modelos Gemini da Google para compreensão e geração de respostas.

🚀 Principais Recursos
🎧 Escuta Contínua com Wake Word

Permanece em modo de espera aguardando a palavra de ativação "assistente". Após a detecção, escuta o comando do usuário, processa a solicitação e retorna automaticamente ao modo de espera.

⚡ Reconhecimento de Voz Local

Utiliza Faster-Whisper executado localmente na CPU para transcrever áudio em português brasileiro, sem dependência de APIs externas de reconhecimento de fala.

🎙️ Captura de Áudio Nativa

Captação direta do microfone utilizando:

sounddevice
numpy

Configuração padrão:

Mono
16 kHz
Baixa latência
🧠 Inteligência Artificial Multimodal

Processa comandos utilizando o Gemini 2.5 Flash, fornecendo respostas rápidas, contextualizadas e precisas.

🗣️ Síntese de Voz Natural

Prioriza a geração de voz através do Edge-TTS e utiliza automaticamente a síntese nativa do Windows (SAPI) como alternativa quando necessário.

🛠️ Tecnologias Utilizadas
Linguagem
Python 3.13+
Inteligência Artificial
google-genai (Gemini API)
Captura e Reconhecimento de Voz
Faster-Whisper
sounddevice
numpy
Síntese de Voz
edge-tts
pygame / pygame-ce
Windows SAPI
Arquitetura
Programação assíncrona
Sistema modular baseado em eventos
⚙️ Instalação
1. Criar e ativar ambiente virtual
PowerShell
python -m venv .venv
.\.venv\Scripts\activate
2. Instalar dependências
PowerShell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
🔑 Configuração da API Gemini

Defina sua chave da API através da variável de ambiente:

PowerShell
PowerShell
$env:GEMINI_API_KEY="sua-api-key"
CMD
BAT
set GEMINI_API_KEY=sua-api-key

Também é possível configurar a variável em um arquivo .env na raiz do projeto.

A variável definida no ambiente possui prioridade sobre o arquivo .env.

▶️ Executando o Assistente
PowerShell
.\.venv\Scripts\python.exe main.py
🧪 Executando os Testes
PowerShell
.\.venv\Scripts\python.exe -m unittest -v test_listener test_local_ops test_cognition test_tts
Teste do Sistema de Voz
PowerShell
.\.venv\Scripts\python.exe tts_smoke_test.py
📌 Status do Projeto

Versão atual: 1.0

A arquitetura foi reestruturada para maximizar desempenho, estabilidade e compatibilidade com versões recentes do Python e do Windows.

🤝 Contribuição

Contribuições são bem-vindas.

Sinta-se à vontade para abrir Issues, enviar Pull Requests ou sugerir novas funcionalidades para o Morpheu.
