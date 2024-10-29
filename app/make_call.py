import sys
import pjsua2 as pj
import logging
import time
from libs import call
from libs import account
from libs import endpoint

# Classe adaptadora para compatibilizar o logger do Python com o log do pjsua2.
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
        #self.epConfig.logConfig.writer = self.log_writer
        self.epConfig.logConfig.level = 5
        self.epConfig.logConfig.consoleLevel = 5

        # Criação de contas e lista de destinatários.
        self.accounts = []
        self.buddy = None

    def start(self):
        # Inicializa a biblioteca.
        self.ep.libInit(self.epConfig)
        # Configurar dispositivo de áudio
        self.ep.audDevManager().setNullDev()
        # Configuração dos transportes.
        transportConfig = pj.TransportConfig()
        self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transportConfig)

        self.ep.libStart()
        self.log_writer.logger.info("Sistema iniciado. Aguardando comandos.")

    def add_account(self, username, password, domain, buddy_uri):
        # Cria e registra uma nova conta.
        acc_cfg = pj.AccountConfig()
        acc_cfg.idUri = f"sip:{username}@{domain}"
        
        # Configuração de Registro
        reg_cfg = acc_cfg.regConfig
        reg_cfg.registrarUri =  f"sip:{domain}" 
        
        # Configuração SIP
        sip_cfg = acc_cfg.sipConfig
        sip_cfg.authCreds.append(pj.AuthCredInfo("digest", "*", username, 0, password))


        self.log_writer.logger.info(f"Conta idUri: {acc_cfg.idUri}")
        self.log_writer.logger.info(f"Conta registrarUri: {acc_cfg.regConfig.registrarUri}")
        acc = account.Account(self)
        acc.create(acc_cfg)
        self.accounts.append(acc)

        self.log_writer.logger.info(f"Conta adicionada: {username}@{domain}")
        #return acc
        time.sleep(10)
        if acc.isRegistered():  # Método fictício, verifique a implementação real
            self.log_writer.logger.info("Registro bem-sucedido.")
            return True
        else:
            self.log_writer.logger.error("Erro: Falha no registro.")
            print("Erro: Falha no registro.")
            return False        

    def make_call(self, buddy_uri, wav_file):
        # Realiza uma ligação para o destinatário especificado.
        if not self.accounts:
            self.log_writer.logger.error("Erro: Nenhuma conta configurada.")
            print("Erro: Nenhuma conta configurada.")
            return
        newcall = call.Call(self.accounts[0], wav_file)  # Usa a primeira conta para a chamada
        call_param = pj.CallOpParam() 
        try:
            newcall.makeCall(buddy_uri,call_param)
            self.log_writer.logger.info(f"Ligação em andamento para: {buddy_uri}")
            time.sleep(40)
        except:
            self.log_writer.logger.error(f"Erro ao ligar para: {buddy_uri}")            
               
        #print(f"Ligação em andamento para: {buddy_uri}")

    def stop(self):
        # Finaliza a biblioteca e o aplicativo.
        self.ep.libDestroy()
        
        self.log_writer.logger.info("Sistema finalizado.")
        print("Sistema finalizado.")

def main(args):
    app = ApplicationCLI()
    app.start()


    if len(args) != 6:
        print(f"Uso: python3 make_call.py <username> <password> <domain> <buddy_uri> <arquivo.wav> {len(args)}")
        return
    
    else:
        username, password, domain, buddy_uri, wav_file = args[1], args[2], args[3], args[4], args[5]
        #app = ApplicationCLI(username, password, domain, buddy_uri, wav_file)
        
    if app.add_account(username, password, domain, buddy_uri):       
        app.make_call(buddy_uri, wav_file)     

if __name__ == "__main__":
    main(sys.argv)
