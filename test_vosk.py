
import json
import wave

from vosk import Model, KaldiRecognizer

modelo = Model("models/vosk-model-small-pt-0.3")

with wave.open("teste_microfone.wav", "rb") as arquivo:
    taxa = arquivo.getframerate()
    reconhecedor = KaldiRecognizer(modelo, taxa)

    while True:
        dados = arquivo.readframes(4000)

        if not dados:
            break

        reconhecedor.AcceptWaveform(dados)

    resultado = json.loads(reconhecedor.FinalResult())

print("Texto reconhecido:", resultado.get("text", ""))
