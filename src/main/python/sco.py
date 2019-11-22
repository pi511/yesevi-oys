from PyQt5.QtWidgets import *
#from PyQt5.QtWebEngineWidgets import QWebEngineSettings
#from PyQt5.QtWebEngineWidgets import QWebEngineView
#from PyQt5.QtNetwork import QNetworkCookieJar


class scoGezgini(QDialog):
    def __init__(self, ctx):
        super(scoGezgini, self).__init__()
        self.ctx = ctx

'''
class flvView(QWebEngineView):
    def __init__(self, ctx, url):
        super(flvView, self).__init__()
        self.ctx=ctx
        QWebEngineSettings.globalSettings().setAttribute( QWebEngineSettings.PluginsEnabled, True)
        cookies=self.ctx.cerezOku()
        self.page().networkAccessManager().setCookieJar(cookies)
        self.load(self, url)
'''