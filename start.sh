#!/bin/bash

# Configurar o Nginx

envsubst '${URL_DOMAIN} ${HTTP_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Criar o arquivo config.conf
makeconfig() {
    echo "[auth]"
    for var in $(compgen -e | grep ^TOKEN_); do
        echo "${var,,} = ${!var}"
    done

    echo ""
    echo "[sip]"
    echo "server_uri = $SIP_SERVER"
    echo "username = $SIP_USERNAME"
    echo "password = $SIP_PASSWORD"
    echo "destination_number = $SIP_DESTINATION"
    
    echo ""
    echo "[tts]"
    echo "language = $TTS_LANG"
    echo "voice = default"

    echo ""
    echo "[queue]"
    echo "time = ${QUEUE_TIME:=15}"
}

makeconfig > /home/webhook/app/config.conf
# Iniciar Nginx
nginx

# Ativar o ambiente virtual
source /home/webhook/app/venv/bin/activate

# Executar o aplicativo Python
cd /home/webhook/app/ && gunicorn --log-level=warning --capture-output --enable-stdio-inheritance -w 4 -b 0.0.0.0:5000 sip-webhook:app