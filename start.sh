#!/bin/bash

# Configurar o Nginx
envsubst '${URL_DOMAIN} ${HTTP_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Função para criar config.conf sem a seção [sip]
makeconfig() {
    echo "[auth]"
    for var in $(compgen -e | grep ^TOKEN_); do
        echo "${var,,} = ${!var}"
    done

    echo ""
    echo "[tts]"
    echo "language = $TTS_LANG"
    echo "voice = default"

    echo ""
    echo "[queue]"
    echo "time = ${QUEUE_TIME:=15}"
}

# Função para criar o arquivo accounts.json usando as variáveis SIP
makeaccounts() {
    cat <<EOF
{
   "accounts": [
      {
         "enabled": true,
         "AccountConfig": {
            "priority": 0,
            "idUri": "sip:${SIP_USERNAME}@${SIP_SERVER}",
            "AccountRegConfig": {
               "registrarUri": "sip:${SIP_SERVER}",
               "registerOnAdd": true,
               "timeoutSec": 300,
               "retryIntervalSec": 300,
               "firstRetryIntervalSec": 0,
               "randomRetryIntervalSec": 10,
               "delayBeforeRefreshSec": 5,
               "dropCallsOnFail": false
            },
            "AccountSipConfig": {
               "authCreds": [
                  {
                     "scheme": "digest",
                     "realm": "*",
                     "username": "${SIP_USERNAME}",
                     "dataType": 0,
                     "data": "${SIP_PASSWORD}"
                  }
               ]
            }
         },
         "buddies": [
            {
               "uri": "sip:${SIP_DESTINATION}@${SIP_SERVER}",
               "priority": 1
            },
            {
               "uri": "sip:outro@${SIP_SERVER}",
               "priority": 2
            }
         ]
      }
   ]
}
EOF
}

# Gerar config.conf e accounts.json
makeconfig > /home/webhook/app/config.conf
makeaccounts > /home/webhook/app/accounts.json

# Iniciar Nginx
nginx

# Ativar o ambiente virtual
source /home/webhook/app/venv/bin/activate

# Executar o aplicativo Python
cd /home/webhook/app/ && python make_call.py && gunicorn --log-level=debug --capture-output --enable-stdio-inheritance -w 4 -b 0.0.0.0:5000 sip-webhook:app