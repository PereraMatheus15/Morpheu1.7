🌌 Morpheu - Assistente Pessoal Multimodal
Um assistente pessoal inteligente e de baixa latência, acionado por voz (usando wake word), projetado para rodar nativamente no Windows sem complicações de compilação. O projeto é integrado aos modelos mais recentes da Google e utiliza síntese de voz natural.

🚀 Funcionalidades Principais
🎧 Escuta Contínua e Wake Word: Fica em modo de espera aguardando a palavra-chave configurada (ex: "Morfeu"). Ao detectá-la, inicia a gravação do comando.

⚡ Captação de Áudio Nativa: Utiliza bibliotecas leves (sounddevice e numpy) para capturar o som diretamente do microfone, dispensando dependências pesadas ou compilações em C++.

🧠 Inteligência Multimodal Avançada: Processa os áudios e comandos utilizando o modelo Gemini 2.5 Flash da Google, garantindo respostas rápidas, contextuais e precisas.

🗣️ Voz Natural e Fluida: Responde às suas solicitações em áudio utilizando o mecanismo de conversão de texto em fala (edge-tts).

🛠️ Tecnologias e Bibliotecas Utilizadas
Linguagem: Python 3.14+

IA & Processamento: google-genai (Gemini API)

Áudio (Captação e Gravação): sounddevice, numpy, wavio

Voz (TTS): edge-tts, pygame

Gerenciamento de Eventos: Arquitetura modular e assíncrona

⚙️ Configuração e Execução
1. Requisitos e Instalação
Certifique-se de estar utilizando um ambiente virtual (.venv) e instale as dependências necessárias:

PowerShell
pip install -r requirements.txt
2. Variáveis de Ambiente
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
python main.py
📌 Status do Projeto
Atualmente na versão 1.0 (v1.py), com o subsistema de escuta ativa e processamento multimodal reestruturados para máxima eficiência e compatibilidade.

Sinta-se à vontade para abrir issues ou enviar pull requests para contribuir com o projeto, Senhor.
