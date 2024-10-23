# Use a imagem base Alpine
FROM alpine:latest

# Instalar dependências básicas
RUN apk update && \
    apk add --no-cache \
        nginx \
        openssl \
        certbot \
        certbot-nginx \
        python3 \
        py3-pip \
        bash \
	pjsua \
	pjproject \
        py3-virtualenv

# Criar um diretório para a aplicação
RUN mkdir -p /home/webhook

# Copiar a aplicação Python para o container
COPY app /home/webhook

# Criar um ambiente virtual e instalar bibliotecas Python necessárias
RUN virtualenv /home/webhook/venv && \
    /home/webhook/venv/bin/pip install --upgrade pip && \
    /home/webhook/venv/bin/pip install flask pyttsx3 configparser

# Configurar Nginx
RUN mkdir -p /run/nginx

# Copiar a configuração do Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Permitir que o Nginx use pastas necessárias
RUN chown -R nginx:nginx /home/webhook

# Definir variáveis de ambiente
ENV URL_DOMAIN=example.com
ENV SSL_ENABLE=false
ENV SSL_CERTBOT_MAIL=your-email@example.com
ENV SIP_SERVER=sip.example.com
ENV SIP_USERNAME=username
ENV SIP_PASSWORD=password
ENV SIP_DESTINATION=destination
ENV TTS_LANG=pt-br
ENV TOKEN_KUMA=uptime_token
ENV TOKEN_OHDEAR=ohdear_token

# Expor as portas HTTP e HTTPS
EXPOSE 80 443

# Configuração de entrada do container
CMD ["/bin/bash", "-c", "/home/webhook/start.sh"]
