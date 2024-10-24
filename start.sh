#!/bin/bash

# Configurar o Nginx

envsubst '${SSL_ENABLE} ${URL_DOMAIN}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

if [ "$SSL_ENABLE" = "true" ]; then
    # Gerar certificado SSL com Certbot
    certbot --nginx -d $URL_DOMAIN --email $SSL_CERTBOT_MAIL --agree-tos --non-interactive
fi

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
}

makeconfig > /home/webhook/app/config.conf
# Iniciar Nginx
nginx

# Ativar o ambiente virtual
source /home/webhook/app/venv/bin/activate

# Executar o aplicativo Python
cd /home/webhook/app/ && python3 sip-webhook.py