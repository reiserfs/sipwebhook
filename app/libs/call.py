import sys
import pjsua2 as pj
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Classe simplificada Call para versão de linha de comando
class Call(pj.Call):
    """
    Objeto de chamada simplificado, derivado do objeto Call do pjsua2.
    """
    # def __init__(self, acc, audio_file, call_id=pj.PJSUA_INVALID_ID):
    #     pj.Call.__init__(self, acc, call_id)
    #     self.acc = acc
    #     self.audio_file = audio_file
    #     self.player = None
    def __init__(self, acc, audio_file):
        super().__init__(acc)
        self.audio_file = audio_file
        self.player = None            

    def onCallState(self, prm):
        ci = self.getInfo()
        #self.connected = ci.state == pj.PJSIP_INV_STATE_CONFIRMED
        logging.info("Estado da chamada atualizado: %s", ci.stateText)
        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            logging.info("*** Mídia de chamada ativa, iniciando reprodução do áudio")
            try:
                self.player = pj.AudioMediaPlayer()
                self.player.createPlayer(self.audio_file, pj.PJMEDIA_FILE_NO_LOOP)
                call_media = self.getAudioMedia(-1)

                # Transmitir áudio do player para a chamada
                self.player.startTransmit(call_media)
            except pj.Error as e:
                print(f"Erro ao transmitir áudio: {e}") 
        if ci.state == pj.PJSIP_INV_STATE_EARLY:    
            self.connected = pj.PJSIP_INV_STATE_CONFIRMED           
        if ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            logging.info("*** Chamada desconectada")        
