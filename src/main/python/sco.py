from PyQt5.QtWidgets import *
from PyQt5 import uic
from lxml import etree
import requests

#from PyQt5.QtWebEngineWidgets import QWebEngineSettings
#from PyQt5.QtWebEngineWidgets import QWebEngineView
#from PyQt5.QtNetwork import QNetworkCookieJar
adres = 'http://sanal.yesevi.edu.tr'

class scoGezgini(QDialog):
    def __init__(self, ctx):
        super(scoGezgini, self).__init__()
        self.ctx = ctx
        uic.loadUi(self.ctx.get_resource('scoExplore.ui'), self)
        self.getMyMeetings()
        self.exec()

    def getMyMeetings(self):
        if self.ctx.online:
            yanit = requests.get(adres + '/report-my-meetings')
            sayfa = yanit.text
            self.responseYaz(self.ctx.anaKlasor + '\\oys-meetings.xml', sayfa)
        else:
            with open(self.ctx.anaKlasor + '\\oys-meetings.xml', 'r', encoding="utf8") as dosya:
                sayfa = dosya.read()
                dosya.close()
        xmlT = etree.fromstring(sayfa)
        print(xmlT.xpath('my-meetings'))
        for i in xmlT.xpath('my-meetings'): print(i.xpath('//name').text)
        print(xmlT.xpath('//results'))
        print(xmlT.xpath('//status'))
        print(xmlT.xpath('//meeting'))
        print(xmlT.xpath('//meeting/url-path'))



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


if __name__ == '__main__':
    print('main.py çalıştır')


