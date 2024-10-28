import sys
import pjsua2 as pj
import os
import time

# Redirecionar a saída para o arquivo call-debug.log
log_file = open("call-debug.log", "a")
sys.stdout = log_file
sys.stderr = log_file

if len(sys.argv) != 6:
    print("Uso: python3 make_call.py <server_uri> <username> <password> <destination_number> <audio_file>")
    sys.exit(1)

server_uri = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]
destination_number = sys.argv[4]
audio_file = sys.argv[5]

class MinhaConta(pj.Account):
    def onRegState(self, prm):
        app.logger.info("*** Estado de registro: " + prm.reason)

class MinhaChamada(pj.Call):
    def __init__(self, conta, audio_file):
        super().__init__(conta)
        self.audio_file = audio_file
        self.player = None

    def onCallState(self, prm):
        ci = self.getInfo()
        app.logger.info(f"*** Estado da chamada: {ci.stateText} ({ci.lastReason})")
        if ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            app.logger.info("*** Chamada desconectada")

    def onCallMediaState(self, prm):
        ci = self.getInfo()

        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            app.logger.info("*** Mídia de chamada ativa, iniciando reprodução do áudio")
            try:
                self.player = pj.AudioMediaPlayer()
                self.player.createPlayer(self.audio_file, pj.PJMEDIA_FILE_NO_LOOP)
                call_media = self.getAudioMedia(-1)

                # Transmitir áudio do player para a chamada
                self.player.startTransmit(call_media)
            except pj.Error as e:
                app.logger.error(f"Erro ao transmitir áudio: {e}")

ep = pj.Endpoint()
try:
    # Configurar e fazer a ligação
    ep_cfg = pj.EpConfig()
    ep.libCreate()
    ep.libInit(ep_cfg)

    # Configurar dispositivo de áudio
    ep.audDevManager().setNullDev()

    # Criar o transporte SIP
    sip_tp_cfg = pj.TransportConfig()
    sip_tp_cfg.port = 5060
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sip_tp_cfg)

    # Iniciar a biblioteca
    ep.libStart()

    # Configuração da conta SIP
    acfg = pj.AccountConfig()
    acfg.idUri = f"sip:{username}@{server_uri}"
    acfg.regConfig.registrarUri = f"sip:{server_uri}"
    cred = pj.AuthCredInfo("digest", "*", username, 0, password)

    acfg.sipConfig.authCreds.append(cred)
    conta = MinhaConta()
    conta.create(acfg)

    # Configurar a chamada
    chamada = MinhaChamada(conta, audio_file)
    call_prm = pj.CallOpParam()
    chamada.makeCall(f"sip:{destination_number}@{server_uri}", call_prm)

    # Manter a biblioteca ativa durante a chamada
    time.sleep(30)  # Mantenha o tempo necessário para a chamada
    # Verifique o estado da chamada antes de destruí-la
    if chamada.getInfo().state != pj.PJSIP_INV_STATE_DISCONNECTED:
        chamada.hangup()  # Encerre a chamada se ainda estiver ativa

    os.remove(audio_file)
except pj.Error as e:
    app.logger.error(f"Erro PJSUA: {e}")
finally:
    ep.libDestroy()  # Garanta que a biblioteca é destruída no final
    log_file.close()  # Fechar o arquivo de log
