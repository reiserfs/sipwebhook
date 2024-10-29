import sys
import random
import pjsua2 as pj

class Account(pj.Account):
    def __init__(self, app):
        pj.Account.__init__(self)
        self.app = app
        self.randId = random.randint(1, 9999)
        self.cfg = pj.AccountConfig()
        self.cfgChanged = False
        self.deleting = False
        self.registered = False  # Novo atributo para rastrear o estado de registro

    def statusText(self):
        status = '?'
        if self.isValid():
            ai = self.getInfo()
            if ai.regLastErr:
                status = self.app.ep.utilStrError(ai.regLastErr)
            elif ai.regIsActive:
                status = "Online" if ai.onlineStatus else "Registered"
            else:
                status = "Unregistered" if ai.regIsConfigured else "Doesn't register"
        else:
            status = '- not created -'
        return status

    def onRegState(self, prm):
        print("Account registration state updated: " + prm.reason)
        self.registered = (prm.code == 200)  # Atualiza o estado de registro com base no código de resposta

    def isRegistered(self):
        return self.registered
