from flask import Flask, request, jsonify
import threading
import time
import queue
import subprocess
import configparser
import os
import tempfile
import pyttsx3
import datetime

# Configuração do Flask
app = Flask(__name__)

# Carregar configurações do arquivo config.conf
config = configparser.ConfigParser()
config.read('config.conf')

# Configurações
token_auth = config['auth']
server_uri = config['sip']['server_uri']
username = config['sip']['username']
password = config['sip']['password']
destination_number = config['sip']['destination_number']

# Fila de mensagens
message_queue = queue.Queue()

# Tempo para a próxima verificação de chamadas em segundos
check_interval = 5
last_call_time = None  # Inicializa a variável como None

def gerar_audio_tts(texto):
    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        engine.setProperty('voice', 95)
        engine.setProperty('rate', 100)
        engine.setProperty('volume', 1.0)        
        engine.save_to_file(texto, temp_file.name)
        engine.runAndWait()
        return temp_file.name

# Função para verificar e fazer ligações a cada minuto
def process_call_queue():
    while True:
        if not message_queue.empty():
            messages = []
            while not message_queue.empty():
                messages.append(message_queue.get())

            # Fazer a ligação e falar as mensagens
            tts_text = f"Você tem {len(messages)} mensagens para ouvir. " + " ".join(messages)
            audio_file = gerar_audio_tts(tts_text)

            # Executar o script para fazer a chamada
            try:
                subprocess.Popen(
                    ["python3", "make_call.py", server_uri, username, password, destination_number, audio_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"Comando de chamada iniciado para {destination_number}")
            except Exception as e:
                print(f"Erro ao iniciar o script de chamada: {e}")

            # Limpar a fila
            os.remove(audio_file)
            print("Fila processada e áudio removido.")

        time.sleep(check_interval)

# Função para lidar com requisições de webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    token = request.headers.get('Authorization')
    message = data.get('message')

    if token in config['auth'].values() and message:
        # Adicionar a mensagem à fila
        message_queue.put(message)
        return jsonify({'status': 'Mensagem adicionada à fila'}), 200
    else:
        return jsonify({'error': 'Token inválido ou mensagem ausente'}), 403

# Rota para verificar o estado da fila
@app.route("/status", methods=["POST"])
def status():
    token = request.headers.get("Authorization")
    if token not in config['auth'].values():
        return jsonify({"error": "Token inválido"}), 401

    queue_size = message_queue.qsize()
    time_remaining = (
        (last_call_time + datetime.timedelta(seconds=check_interval) - datetime.datetime.now()).total_seconds()
        if last_call_time
        else "Nenhuma ligação feita"
    )

    return jsonify(
        {
            "queue_size": queue_size,
            "destination_number": destination_number,
            "time_remaining": time_remaining,
        }
    ), 200

# Inicializar o processamento da fila em uma thread separada
call_thread = threading.Thread(target=process_call_queue)
call_thread.daemon = True
call_thread.start()

# Iniciar o servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)