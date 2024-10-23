#!/bin/bash

# Configurar o Nginx
if [ "$SSL_ENABLE" = "true" ]; then
    # Gerar certificado SSL com Certbot
    certbot --nginx -d $URL_DOMAIN --email $SSL_CERTBOT_MAIL --agree-tos --non-interactive
fi

# Atualizar config.conf com variáveis de ambiente
sed -i "s/SEU_TOKEN_UPTIME_KUMA/$TOKEN_KUMA/g" /home/webhook/config.conf
sed -i "s/SEU_TOKEN_GRAFANA/$TOKEN_KUMA/g" /home/webhook/config.conf
sed -i "s/SEU_TOKEN_OHDEAR/$TOKEN_OHDEAR/g" /home/webhook/config.conf
sed -i "s/TOKEN_STATUS/$TOKEN_STATUS/g" /home/webhook/config.conf
sed -i "s/server_uri = .*/server_uri = $SIP_SERVER/g" /home/webhook/config.conf
sed -i "s/username = .*/username = $SIP_USERNAME/g" /home/webhook/config.conf
sed -i "s/password = .*/password = $SIP_PASSWORD/g" /home/webhook/config.conf
sed -i "s/destination_number = .*/destination_number = $SIP_DESTINATION/g" /home/webhook/config.conf
sed -i "s/language = .*/language = $TTS_LANG/g" /home/webhook/config.conf

# Iniciar Nginx
nginx

# Iniciar a aplicação Python
python3 /home/webhook/app/main.py

