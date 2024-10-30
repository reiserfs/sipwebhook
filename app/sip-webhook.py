from flask import Flask, request, jsonify, render_template, make_response
from flasgger import Swagger
import configparser
import os
import tempfile
import pyttsx3
import datetime
import json
import logging
import hashlib
from datetime import datetime

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
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "headers": []
}
Swagger(app, config=swagger_config)

# Carregar configurações do arquivo config.conf
config = configparser.ConfigParser()
config.read('config.conf')

# Configurações
token_auth = config['auth']

# Adicionar filtro de formatação de data
def format_datetime(value):
    try:
        # Tentar com o formato ISO com fração de segundo
        dt = datetime.fromisoformat(value)
    except ValueError:
        # Caso não funcione, usar o formato simples de data e hora
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%d/%m/%Y %H:%M")

app.jinja_env.filters['datetimeformat'] = format_datetime

# Função para gerar o áudio em TTS e salvar
def gerar_audio_tts(texto):
    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        engine.setProperty('voice', 95)
        engine.setProperty('rate', 100)
        engine.setProperty('volume', 1.0)        
        engine.save_to_file(texto, temp_file.name)
        engine.runAndWait()
        app.logger.info(f"Áudio criado em: {temp_file.name}")
        return temp_file.name

# Função para receber a mensagem e salvar em JSON
def receive_message(token, message_text):
    # Encontrar a chave correspondente ao token
    token_key = next((key for key, value in config['auth'].items() if value == token), None)

    # Carregar dados existentes do JSON, se houver
    if os.path.exists("messages.json"):
        with open("messages.json", "r") as f:
            all_messages = json.load(f)
    else:
        all_messages = []

    # Dados da nova mensagem
    message_data = {
        "token_used": token_key,
        "created_at": datetime.datetime.now().isoformat(),
        "message_text": message_text,
        "temp_wav_location": gerar_audio_tts(message_text),
        "status": "received",
        "call_data": []
    }

    # Adicionar nova mensagem à lista e salvar
    all_messages.append(message_data)
    with open("messages.json", "w") as f:
        json.dump(all_messages, f, indent=4)

    app.logger.info("Dados salvos em messages.json")
    return message_data

# Função para carregar o JSON
def load_messages():
    if os.path.exists("messages.json"):
        with open("messages.json", "r") as f:
            return json.load(f)
    return []

# Função para salvar o JSON atualizado
def save_messages(messages):
    with open("messages.json", "w") as f:
        json.dump(messages, f, indent=4)    

# Função para gerar hash MD5 do token para cookie
def generate_md5_token(token):
    return hashlib.md5(token.encode()).hexdigest()

# Rota para o webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Receber notificações e adicionar mensagem ao JSON.
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
        description: Mensagem a ser adicionada ao JSON
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
        message_data = receive_message(token, message)
        return jsonify(message_data), 200
    else:
        app.logger.error('Token inválido ou mensagem ausente')
        return jsonify({'error': 'Token inválido ou mensagem ausente'}), 403

# Rota para verificar o estado do JSON
@app.route("/status", methods=["POST"])
def status():
    """
    Verificar o estado da fila no JSON.
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
            data:
              type: array
      401:
        description: Token inválido
    """
    token = request.headers.get("Authorization")
    if token not in config['auth'].values():
        app.logger.info('status - "Token inválido"')  
        return jsonify({"error": "Token inválido"}), 401

    # Carregar dados do arquivo JSON
    if os.path.exists("messages.json"):
        with open("messages.json", "r") as f:
            data = json.load(f)
    else:
        data = {"error": "Arquivo messages.json não encontrado"}

    return jsonify(data), 200

# Rota para o portal HTML com a tabela
@app.route("/", methods=["GET"])
def portal():
    # token = request.headers.get("Authorization")
    # if token not in config['auth'].values():
    #     app.logger.info('status - "Token inválido"')  
    #     return jsonify({"error": "Token inválido"}), 401

    # Carregar dados do JSON
    messages = load_messages()
    has_called = any(msg['status'] == 'called' for msg in messages)

    # Renderizar o template HTML com dados
    return render_template("portal.html", messages=messages, has_called=has_called)

# Rota para atualizar status de 'called' para 'answered'
@app.route("/attend_calls", methods=["POST"])
def attend_calls():
    # token = request.headers.get("Authorization") or request.cookies.get("auth_cookie")
    # valid_token = any(generate_md5_token(v) == token for v in token_auth.values())

    # if not valid_token:
    #     return jsonify({"success": False, "error": "Unauthorized"}), 401

    messages = load_messages()
    updated = False

    # Atualizar todas as mensagens 'called' para 'answered'
    for msg in messages:
        if msg['status'] == 'called':
            msg['status'] = 'answered'
            updated = True

    if updated:
        save_messages(messages)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No messages to update"})

# Iniciar o servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
