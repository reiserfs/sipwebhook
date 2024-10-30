import sys
import pjsua2 as pj
import logging
import time
import json
from datetime import datetime
from libs import call
from libs import account
from libs import endpoint

class LogWriterAdapter(pj.LogWriter):
    """
    Logger to receive log messages from pjsua2
    """
    def __init__(self):
        logging.basicConfig(filename="app.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()
        pj.LogWriter.__init__(self)

    # Método correto para capturar o log do pjsua2.
    def write(self, entry, level=None):
        self.logger.info(entry.msg)

class ApplicationCLI:
    def __init__(self):
        # Cria o adaptador de log e configurações de log do endpoint.
        self.log_writer = LogWriterAdapter()
        
        # Inicializa o endpoint.
        self.ep = endpoint.Endpoint()
        self.ep.libCreate()

        # Configurações iniciais.
        self.epConfig = pj.EpConfig()
        self.epConfig.logConfig.level = 5
        self.epConfig.logConfig.consoleLevel = 5

        # Criação de contas.
        self.accounts = []

    def start(self):
        # Inicializa a biblioteca.
        self.ep.libInit(self.epConfig)
        self.ep.audDevManager().setNullDev()  # Configure dispositivo de áudio
        transportConfig = pj.TransportConfig()
        self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transportConfig)

        self.ep.libStart()
        self.log_writer.logger.info("Sistema iniciado. Aguardando comandos.")

    def load_accounts(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            for account_data in data["accounts"]:
                if account_data["enabled"]:
                    return account_data                  

    def add_account(self, account_data):
        acc_cfg = pj.AccountConfig()
        acc_cfg.idUri = account_data["AccountConfig"]["idUri"]
        reg_cfg = acc_cfg.regConfig
        reg_cfg.registrarUri = account_data["AccountConfig"]["AccountRegConfig"]["registrarUri"]
        sip_cfg = acc_cfg.sipConfig
        
        for cred in account_data["AccountConfig"]["AccountSipConfig"]["authCreds"]:
            sip_cfg.authCreds.append(pj.AuthCredInfo("digest", cred["realm"], cred["username"], 0, cred["data"]))

        self.log_writer.logger.info(f"Conta idUri: {acc_cfg.idUri}")
        acc = account.Account(self)
        acc.create(acc_cfg)
        self.accounts.append(acc)
        
        time.sleep(10)
        if acc.isRegistered():
            self.log_writer.logger.info("Registro bem-sucedido.")
            return account_data['buddies']
        else:
            self.log_writer.logger.error("Erro: Falha no registro.")

    def read_messages(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)

    def update_message(self, messages, index, call_data, status):
        # Atualiza o JSON da mensagem com o `call_data` e `status`
        messages[index]["call_data"] = call_data
        messages[index]["status"] = status
        with open('messages.json', 'w') as f:
            json.dump(messages, f, indent=4)
        
    def make_calls(self, buddies):
        while True:
            messages = self.read_messages('messages.json')
            for index, message in enumerate(messages):  # Itera diretamente sobre a lista de mensagens
                if message["status"] == "received":
                    for buddy in sorted(buddies, key=lambda b: b.get("priority", 0)):
                        buddy_uri = buddy["uri"]
                        audio_file = message.get("temp_wav_location")
                        self.log_writer.logger.info(f"Fazendo chamada para {buddy_uri} com arquivo {audio_file}")
                        self.make_call(buddy_uri, audio_file, messages, index)  # Passa a mensagem e o índice
                        break  # Para de ligar assim que fizer a primeira chamada
                time.sleep(5)  # Aguarda 5 segundos antes de verificar novamente

    def make_call(self, buddy_uri, wav_file, messages, index):
        if not self.accounts:
            self.log_writer.logger.error("Erro: Nenhuma conta configurada.")
            return

        newcall = call.Call(self.accounts[0], wav_file)  # Usa a primeira conta para a chamada
        call_param = pj.CallOpParam() 
        try:
            newcall.makeCall(buddy_uri, call_param)
            self.log_writer.logger.info(f"Ligação em andamento para: {buddy_uri}")
            time.sleep(10)  # Aguardar 10 segundos para a chamada

            # Obter informações do estado da chamada
            call_info = newcall.getInfo()
            call_state = call_info.stateText
            call_result = "answered" if call_state == "CONFIRMED" else "called"

            # Dados para o `call_data`
            call_data = {
                "last_call": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "number_called": buddy_uri,
                "call_result": call_state
            }
            # Atualiza a mensagem
            self.update_message(messages, index, [call_data], call_result)
            self.log_writer.logger.info(f"Chamada para {buddy_uri} finalizada com estado: {call_state}")

        except Exception as e:
            self.log_writer.logger.error(f"Erro ao ligar para {buddy_uri}: {e}")

    def stop(self):
        self.ep.libDestroy()
        self.log_writer.logger.info("Sistema finalizado.")

def main():
    app = ApplicationCLI()
    app.start()
    app.make_calls(app.add_account(app.load_accounts('accounts.json')))  

if __name__ == "__main__":
    main()
