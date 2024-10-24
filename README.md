# SIP Webhook Application

Esta aplicação permite gerenciar webhooks e realizar chamadas SIP automaticamente com base em notificações recebidas de serviços como Uptime Kuma, Grafana e Oh Dear. Ela utiliza Flask para a API web e PJSUA para realizar as chamadas SIP.

## Funcionalidades

- Receber notificações via Webhook de Uptime Kuma, Grafana e Oh Dear.
- Realizar chamadas SIP com mensagens de texto sintetizado (TTS).
- Documentação automática da API utilizando Swagger.
- Monitoramento do status das notificações e filas de chamadas.

## Configuração

### Pré-requisitos

- Python 3.11+
- Bibliotecas instaladas a partir do `requirements.txt`

### Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu_usuario/sip-webhook.git
   cd sip-webhook```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt```

3. Configure o arquivo config.conf:

O arquivo `config.conf` deve conter as seções para autenticação (`auth`), configuração do servidor SIP (`sip`), e TTS (`tts`). Exemplo:
    ```ini
    [auth]
    uptime_kuma_token = SEU_TOKEN_UPTIME_KUMA
    grafana_token = SEU_TOKEN_GRAFANA
    ohdear_token = SEU_TOKEN_OHDEAR
    token_status = TOKEN_STATUS

    [sip]
    sip_server = sip.example.com
    sip_username = username
    sip_password = password
    sip_destination = destination

    [tts]
    lang = pt-br```

4. Execute a aplicação:

``` bash
gunicorn -w 4 -b 0.0.0.0:5000 sip-webhook:app
```

## Configurando Variáveis de Ambiente no Container

Para utilizar a aplicação em um ambiente Docker, defina as variáveis de ambiente no `Dockerfile` ou no comando de execução do container. Exemplos:

### Configuração no Dockerfile

``` dockerfile
# Definir variáveis de ambiente
ENV URL_DOMAIN=example.com
ENV HTTP_PORT=80
ENV SIP_SERVER=sip.example.com
ENV SIP_USERNAME=username
ENV SIP_PASSWORD=password
ENV SIP_DESTINATION=destination
ENV TTS_LANG=pt-br
ENV TOKEN_KUMA=uptime_token
ENV TOKEN_OHDEAR=ohdear_token
```

### Configuração com o Docker Run

Você também pode configurar as variáveis de ambiente ao executar o container:

``` bash
docker run -d \
  -e URL_DOMAIN=example.com \
  -e HTTP_PORT=80 \
  -e SIP_SERVER=sip.example.com \
  -e SIP_USERNAME=username \
  -e SIP_PASSWORD=password \
  -e SIP_DESTINATION=destination \
  -e TTS_LANG=pt-br \
  -e TOKEN_KUMA=uptime_token \
  -e TOKEN_OHDEAR=ohdear_token \
  -p 5000:80 \
  sip-webhook
```
## Uso

A aplicação expõe endpoints para receber notificações dos serviços configurados. O endpoint principal é `/webhook`, que deve ser chamado pelos serviços de monitoramento.

### Exemplo de chamada ao webhook

``` bash
curl -X POST http://<IP_DO_SERVIDOR>:5000/webhook -H "Authorization: SEU_TOKEN" -d '{"message": "Alerta de serviço"}'
```
### Endpoint de Status

Você pode verificar o estado da aplicação através do endpoint `/status`:

``` bash
curl -X POST http://<IP_DO_SERVIDOR>:5000/status -H "Authorization: TOKEN_STATUS"
```
## Documentação da API

A documentação da API pode ser acessada em `/apidocs`. Certifique-se de que a aplicação esteja em execução e acesse o endpoint para visualizar a documentação interativa.

``` bash
http://<IP_DO_SERVIDOR>:5000/apidocs
```
## Logs

Os logs da aplicação são gerados no console. Você pode redirecionar a saída para um arquivo para facilitar a leitura e depuração:

``` bash
gunicorn -w 4 -b 0.0.0.0:5000 sip-webhook:app > logs/app.log 2>&1
```
