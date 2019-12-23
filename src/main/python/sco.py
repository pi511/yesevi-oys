from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QTextCharFormat,QFont
from lxml import etree
from bs4 import BeautifulSoup
import os
from datetime import datetime
import urllib.parse
# import requests

#from PyQt5.QtWebEngineWidgets import QWebEngineSettings
#from PyQt5.QtWebEngineWidgets import QWebEngineView
#from PyQt5.QtNetwork import QNetworkCookieJar

adres = 'http://sanal.yesevi.edu.tr'
debug = False
DERSSURESI = -90

class scoGezgini(QDialog):
    def __init__(self, ctx):
        global debug
        super(scoGezgini, self).__init__()
        self.ctx = ctx
        uic.loadUi(self.ctx.get_resource('scoExplore.ui'), self)
        debug = self.ctx.debug
        os.makedirs(self.ctx.anaKlasor + '\\sco', exist_ok=True)
        self.dersler=[]
        self.mCount, self.MyMeetings=self.getMyMeetings()
        if self.mCount is None:
            if debug: print(f"scoGezgini: Düzgün xml bulunamadı, online olunacak!")
            self.ctx.onlineOl()
            self.mCount, self.MyMeetings = self.getMyMeetings(self.ctx.oturum)
        self.takvimDoldur()
        self.calTakvim.clicked.connect(self.calClicked)
        self.lstDersler.clicked.connect(self.dersClicked)
        self.buttonBox.accepted.connect(self.dosyaGetir)
        self.exec()

    def getMyMeetings(self, oturum=None):
        myMeetings=[]
        if oturum: poturum='&session='+oturum
        else: poturum=''
        mydosya=self.ctx.anaKlasor + '\\oys-meetings.xml'
        if not os.path.isfile(mydosya) or poturum!='':
            if not self.ctx.onlineOldu: self.ctx.onlineOl()
            url=adres + '/api/xml?action=report-my-meetings'+poturum
            yanit = self.ctx.session.get(url)
            yanit.encoding = 'UTF-8'
            if debug: print(f"getMyMeetings: adres={url}")
            sayfa = yanit.text
            self.ctx.responseYaz(mydosya, sayfa)
        else:
            with open(mydosya, 'r', encoding="utf-8") as dosya:
                sayfa = dosya.read()
                dosya.close()
        try:
            xmlkok = etree.fromstring(bytes(sayfa, encoding='utf-8'))
        except:
            return None, None
        i=0
        for eleman in xmlkok:
            if eleman.tag=='status':
                if eleman.attrib['code']!='ok':
                    if debug: print(f"getMyMeetings: Hata={eleman.attrib['code']} subcode={eleman.attrib['subcode']}")
                    return None, None
            if eleman.tag=='my-meetings':
                xmlkok = eleman
        for meeting in xmlkok:
            myMeetings.append({'no': i})
            myMeetings[i]['sco-id']= meeting.attrib['sco-id']
            for item in meeting:
                if debug and i==0: print(f"getMyMeetings: row-id={meeting.attrib['row-id']} tag{item.tag}= text={item.text}")
                if item.tag=='name': myMeetings[i]['name'] = item.text.strip()
                if item.tag=='description': myMeetings[i]['desc'] = item.text.strip()
                if item.tag=='url-path': myMeetings[i]['url'] = item.text
                if item.tag in ['date-begin','date-end']:
                    tarih = item.text[:10]
                    tarih=datetime.strptime(tarih,'%Y-%m-%d') # format farklı burada self.ctx.gun2date() olmuyor
                if item.tag=='date-begin': myMeetings[i]['dateB'] = tarih
                if item.tag=='date-end': myMeetings[i]['dateE'] = tarih
                if item.tag=='date-end': myMeetings[i]['saat'] = item.text[11:16]
                if item.tag=='expired': myMeetings[i]['expired'] = item.text
            if debug and (i % 11)==0: print(f"getMyMeetings: {myMeetings[i]}")
            i += 1
        self.ctx.logYaz(f"getMyMeetings: {i} adet meeting okundu")
        return i, myMeetings

    def takvimDoldur(self):
        format= QTextCharFormat()
        format.setFontWeight(QFont.Bold)
        self.minDate=self.MyMeetings[0]['dateB']
        self.maxDate=self.MyMeetings[0]['dateE']
        for i in range(1, self.mCount):
            if self.MyMeetings[i]['dateB'] < self.minDate: self.minDate=self.MyMeetings[i]['dateB']
            if self.MyMeetings[i]['dateE'] > self.maxDate: self.maxDate=self.MyMeetings[i]['dateB']
            if self.MyMeetings[i]['expired'] : self.calTakvim.setDateTextFormat(self.MyMeetings[i]['dateB'], format)
        self.calTakvim.setMinimumDate(self.minDate)
        self.calTakvim.setMaximumDate(self.maxDate)
        # self.calTakvim.setMaximumDate(datetime.today())
        self.calTakvim.showToday()

    def calClicked(self):
        self.lstDersler.clear()
        self.dersler=[]
        for i in range(0, self.mCount):
            if self.calTakvim.selectedDate() == self.MyMeetings[i]['dateB']:
                self.lstDersler.addItem(self.MyMeetings[i]['name'])
                self.dersler.append(self.MyMeetings[i]['sco-id'])
                self.MyMeeting = self.MyMeetings[i]
        # self.lstDosyalar

    def getDosyalar(self, scoId, oturum=None):
        dosyalar = []
        refler = {}
        if oturum: poturum='&session='+oturum
        else: poturum=''
        scodosya=self.ctx.anaKlasor + f'\\sco\\oys-scoexp{scoId}.xml'
        if not os.path.isfile(scodosya) or poturum!='':
            if not self.ctx.onlineOldu: self.ctx.onlineOl()
            url= adres + '/api/xml?action=sco-expanded-contents&sco-id=' + scoId + poturum
            if oturum is None:
                yanit = self.ctx.session.get(url)
                yanit.encoding = 'UTF-8'
            else:
                yanit = self.ctx.session.get(url, cookies=self.ctx.cerezler)
                yanit.encoding = 'UTF-8'
            if debug: print(f"getDosyalar: adres={url}")
            sayfa = yanit.text
            self.ctx.responseYaz(scodosya, sayfa)
        else:
            with open(scodosya, 'r', encoding="utf-8") as dosya:
                sayfa = dosya.read()
                dosya.close()
        try:
            xmlkok= etree.fromstring(bytes(sayfa,encoding='utf-8'))
        except:
            if debug: print(f"getDosyalar: Dosya bozuk, tekrar indirilecek")
            self.ctx.onlineOl()
            i, dosyalar = self.getDosyalar(scoId,self.ctx.oturum)
            return i, dosyalar
        i=0
        ekle= True
        for eleman in xmlkok:
            if eleman.tag=='status':
                if eleman.attrib['code']!='ok':
                    if debug: print(f"getDosyalar: Hata={eleman.attrib['code']} subcode={eleman.attrib['subcode']}")
                    self.ctx.onlineOl()
                    i, dosyalar = self.getDosyalar(scoId, self.ctx.oturum)
                    return i, dosyalar
            if eleman.tag=='expanded-scos':
                xmlkok = eleman
        for dosya in xmlkok:
            if ekle: dosyalar.append({'no': i})
            ekle= False
            for item in dosya:
                if debug and i==0: print("getDosyalar: depth=",dosya.attrib['depth'],"type=",dosya.attrib['type'],"tag=",item.tag,"text=",item.text)
                if item.tag=='seminar-name':
                    dosyalar[i]['dosyaadi']=item.text.strip()
                    ekle= True
                if dosya.attrib['depth'] != '1': ekle= False
                dosyalar[i]['scoid']= dosya.attrib['sco-id']
                if item.tag=='url-path': dosyalar[i]['url']=item.text.strip()
            dosyalar[i]['depth'] = dosya.attrib['depth']
            refler[dosyalar[i]['url'][1:-1]] = dosyalar[i]['dosyaadi']
            if dosyalar[i]['dosyaadi'][0] + dosyalar[i]['dosyaadi'][-1] == '//':
                if debug: print("reflerde varmı=", dosyalar[i]['dosyaadi'][1:-1] in refler, "refler=", refler)
                while dosyalar[i]['dosyaadi'][1:-1] in refler:
                    dosyalar[i]['dosyaadi']=refler[dosyalar[i]['dosyaadi'][1:-1]]
            if debug: print(f"getDosyalar: {dosyalar[i]}")
            if ekle: i += 1
        self.ctx.logYaz(f"getDosyalar: {scodosya}= {i} adet dosya okundu")
        return i+1, dosyalar

    def dersClicked(self, index):
        self.lstDosyalar.clear()
        cik= False
        if self.ctx.bugunmu( self.ctx.date2gun( self.MyMeeting['dateE'] ) ) and self.ctx.kalanDakika( self.MyMeeting['saat'] ) >= DERSSURESI: cik = True
        elif self.MyMeeting['dateE'] > datetime.now(): cik = True
        if cik:
            if debug: print(f"dersClicked: Ders henüz işlenmemiş...tarih={ self.ctx.date2gun( self.MyMeeting['dateE'] ) } saat={self.MyMeeting['saat']}")
            return
        c, dosyalar=self.getDosyalar(self.dersler[index.row()])
        if c is None:
            self.ctx.onlineOl()
            c, dosyalar = self.getDosyalar(self.dersler[index.row()],self.ctx.oturum)
        for i in range(0,c):
            self.lstDosyalar.addItem(f"{dosyalar[i]['dosyaadi']} ({dosyalar[i]['depth']})")
        self.dosyalar=dosyalar

    def setHeaders(self):
        header={'Connection': 'keep-alive',
                'Host': 'sanal.yesevi.edu.tr',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br'}
        header['Cookie']=f"BreezeCCookie={self.ctx.cerezler['BreezeCCookie']}; BreezeLoginCookie=; BREEZESESSION={self.ctx.cerezler['BREEZESESSION']}"
        if debug: print(f"setHeaders: {header}")
        return header

    def readable_size(self, size):
        if type(size)==type(None):
            size = 0
        units = ('KB', 'MB', 'GB', 'TB')
        size_list = [f'{int(size):,d} B'] + [f'{int(size) / 1024 ** (i + 1):,.1f} {u}' for i, u in enumerate(units)]
        return [size for size in size_list if not size.startswith('0.')][-1]

    def dosyaGetir(self):
        self.buttonBox.Cancel= True
        if self.lstDosyalar.selectedIndexes()==[]:
            self.buttonBox.Cancel = False
            if debug: print(f"dosyaGetir: Seçili dosya yok!")
            return
        d=self.lstDosyalar.selectedIndexes()[0].row()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.ctx.onlineOl()
        dosyaadi = self.dosyalar[d]['dosyaadi']
        url = f"{adres}{self.dosyalar[d]['url']}source/{urllib.request.pathname2url(dosyaadi)}" + '?session=' + self.ctx.oturum
        yanit= self.ctx.session.get(url, headers=self.setHeaders())
        yanit.encoding = 'UTF-8'
        durum = yanit.status_code
        dosyaboyu = yanit.headers.get('content-length')
        if debug: print(f"dosyaGetir: ilk deneme={durum} dosyaboyutu={self.readable_size(dosyaboyu)} ({dosyaboyu} bytes)")
        yanit = self.ctx.session.get(url, stream= True, headers=self.setHeaders())  #ikinci deneme, ilk denemede inmiyor genelde
        yanit.encoding = 'UTF-8'
        durum = yanit.status_code
        if debug: print(f"dosyaGetir: gelenHeader={yanit.headers}")
        # import urllib.request
        # yanit = urllib.request.urlopen(url)
        # durum=yanit.getcode()
        self.ctx.TimedMessageBox('scoGezgini', f'Ekran uzun süre hareketsiz kalabilir, lütfen bekleyiniz.', QMessageBox.Ok, 3)
        soup=BeautifulSoup(yanit.text[:100],'html.parser')
        sonuc=soup.find('title')
        if sonuc: sonuc=sonuc.text
        if debug: print(f"dosyaGetir: durum={durum} dosyaadi={dosyaadi} url={url} sonuc={sonuc}")
        if durum != 200 or sonuc=='Bulunamadı':
            dosyaadi = f"{self.dosyalar[d]['scoid']}.zip"
            url = f"{adres}{self.dosyalar[d]['url']}output/{dosyaadi}?download=zip" + '&session=' + self.ctx.oturum
            yanit = self.ctx.session.get(url, cookies=self.ctx.cerezler, stream= True)
            yanit.encoding = 'UTF-8'
            durum = yanit.status_code
            soup=BeautifulSoup(yanit.text[:100],'html.parser')
            sonuc=soup.find('title')
        else:
            self.ctx.logYaz(f"dosyaGetir: durum={durum} dosyaadi={dosyaadi} url={url} sonuc={sonuc}")
        if debug: print(f"dosyaGetir: durum={durum} dosyaadi={dosyaadi} url={url} sonuc={sonuc}")
        if durum != 200 or sonuc=='Bulunamadı':
            self.ctx.TimedMessageBox('scoGezgini', f'Dosya bulunamadı', QMessageBox.Ok, 3)
            return
        else:
            self.ctx.logYaz(f"dosyaGetir: durum={durum} dosyaadi={dosyaadi} url={url} sonuc={sonuc}")
        fileName, _ = QFileDialog.getSaveFileName(self, "scoGezgini - Dosya Kaydet", self.ctx.anaKlasor +'\\' + dosyaadi ,"All Files (*)", options=options)
        if fileName:
            with open(fileName, 'wb') as dosya:
                for chunk in yanit.iter_content(chunk_size=512):
                    dosya.write(chunk)
            self.ctx.TimedMessageBox('scoGezgini', f'Dosya kaydedildi: {fileName}', QMessageBox.Ok, 3)


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


