from flask import Flask, request, jsonify
from flasgger import Swagger
import threading
import time
import queue
import subprocess
import configparser
import os
import tempfile
import pyttsx3
import datetime
import logging

# Configuração do Flask
app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

swagger_config = {
    "swagger": "2.0",
    "info": {
        "title": "SIP Webhook API",
        "description": "API para gerenciar webhooks e chamadas SIP",
        "version": "1.0.0"
    },
    "host": "localhost:5000",  # Altere conforme necessário
    "basePath": "/",
    "schemes": [
        "http"
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # Todos os endpoints são documentados
            "model_filter": lambda tag: True,  # Todos os modelos são documentados
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "headers": []  # Adicionando uma lista vazia para evitar o erro
}
Swagger(app, config=swagger_config)

# Carregar configurações do arquivo config.conf
config = configparser.ConfigParser()
config.read('config.conf')

# Configurações
token_auth = config['auth']
server_uri = config['sip']['server_uri']
username = config['sip']['username']
password = config['sip']['password']
destination_number = config['sip']['destination_number']
queue_time = config['queue']['time']

# Fila de mensagens
message_queue = queue.Queue()

# Tempo para a próxima verificação de chamadas em segundos
check_interval = int(queue_time)
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
                app.logger.info(f"Comando de chamada iniciado para {destination_number}")
            except Exception as e:
                app.logger.error(f"Erro ao iniciar o script de chamada: {e}")

            # Limpar a fila
            os.remove(audio_file)
            app.logger.info("Fila processada e áudio removido.")

        time.sleep(check_interval)

# Função para lidar com requisições de webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Receber notificações e adicionar mensagem à fila.
    ---
    tags:
      - Webhook
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Token de autenticação
      - name: message
        in: body
        type: string
        required: true
        description: Mensagem a ser adicionada à fila
    responses:
      200:
        description: Mensagem adicionada com sucesso
      403:
        description: Token inválido ou mensagem ausente
    """    
    data = request.json
    token = request.headers.get('Authorization')
    message = data.get('message')

    if token in config['auth'].values() and message:
        # Adicionar a mensagem à fila
        message_queue.put(message)
        app.logger.info('status: Mensagem adicionada à fila')
        return jsonify({'status': 'Mensagem adicionada à fila'}), 200
    else:
        app.logger.error('error: Token inválido ou mensagem ausente')
        return jsonify({'error': 'Token inválido ou mensagem ausente'}), 403

# Rota para verificar o estado da fila
@app.route("/status", methods=["POST"])
def status():
    """
    Verificar o estado da fila.
    ---
    tags:
      - Status
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: Token de autenticação
    responses:
      200:
        description: Estado da fila
        schema:
          type: object
          properties:
            queue_size:
              type: integer
            destination_number:
              type: string
            time_remaining:
              type: string
      401:
        description: Token inválido
    """    
    token = request.headers.get("Authorization")
    if token not in config['auth'].values():
        app.logger.info('status - "Token inválido"')  
        return jsonify({"error": "Token inválido"}), 401

    queue_size = message_queue.qsize()
    time_remaining = (
        (last_call_time + datetime.timedelta(seconds=check_interval) - datetime.datetime.now()).total_seconds()
        if last_call_time
        else "Nenhuma ligação feita"
    )
    app.logger.info('status - return')  
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
