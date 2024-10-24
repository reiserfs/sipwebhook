#!/bin/bash

# Configurar o Nginx

# Substituir variáveis de ambiente no arquivo de configuração do Nginx
if [ "$SSL_ENABLE" = "true" ]; then
    # Adicionar configuração de SSL ao nginx.conf
    envsubst '${URL_DOMAIN}' < /etc/nginx/nginx.conf.ssl > /etc/nginx/nginx.conf
    # Gerar certificado SSL com Certbot
    certbot --nginx -d $URL_DOMAIN --email $SSL_CERTBOT_MAIL --agree-tos --non-interactive    
else
    # Usar a configuração básica sem SSL
    envsubst '${URL_DOMAIN}' < /etc/nginx/nginx.conf.no-ssl > /etc/nginx/nginx.conf
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
cd /home/webhook/app/ && gunicorn -w 4 -b 127.0.0.1:5000 sip-webhook:app