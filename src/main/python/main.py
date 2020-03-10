# coding=utf-8
from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
import base64
# import sys
# import os
import webbrowser
# from datetime import datetime, timedelta
import configparser
import pickle
# import requests
import requests.cookies
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSlot
#from PyQt5.QtWidgets import *
# from bs4 import BeautifulSoup
import sqlite3
from sco import *
from dersIcerik import *
from dersArsiv import *

debug = False
anaKlasor = os.environ['USERPROFILE']+'\\oys-yesevi'
ayarlar = anaKlasor + '\\oys-yesevi.ini'
cerezF = anaKlasor + '\\oys-yesevi-c.ini'
logfile = anaKlasor + '\\oys-yesevi.log'
dbfile = anaKlasor + '\\oys-yesevi.db'
Config = configparser.ConfigParser()
adres = 'https://oys.yesevi.edu.tr'
dersler = []
ilkders = -1
ONLINESURE = 10


class AppContext(ApplicationContext):
    def __init__(self):
        super(AppContext, self).__init__()
        self.online = True
        self.onlineOldu = False
        #global değişkenleri buraya alabilirsin

    def run(self):
        self.ctx = appctxt
        self.main_window.show()
        return self.app.exec_()

    @cached_property
    def main_window(self):
        self.app.setApplicationName('OYS')
        return AnaPencere(self)

    def setOnline(self,online): #Hayır-Evet -> False-True
        if online == 'Hayir':
            self.ctx.online = False  # sayfaları internetten mi alsın, kayıttan mı?
        else:
            self.ctx.online = True
        return self.ctx.online

    def getOnline(self, online=None): #False-True -> Hayır-Evet
        return 'Evet' if (self.ctx.online if online is None else online) else 'Hayir'

    class Ayarlar(QDialog):
        def __init__(self, ctx):
            global debug
            super(QDialog, self).__init__()
            self.ctx = ctx
            # uic.loadUi('Ayarlar.ui',self)
            uic.loadUi(self.ctx.get_resource('Ayarlar.ui'), self)
            self.debug = debug
            self.dersDakika = self.ctx.dersDakika
            self.spnDakika.setValue(self.ctx.dersDakika)
            self.cbxDebug.setChecked(debug)
            self.online = self.ctx.online
            self.cbxOnline.setChecked(self.online)
            self.minSaat = self.ctx.minSaat
            self.maxSaat = self.ctx.maxSaat
            self.spnTimerDk.setValue(self.ctx.TimerDk)
            self.spnGuncellemeDk.setValue(self.ctx.GuncellemeDk)
            self.radKaynak.setChecked(False if self.ctx.dpKaynak=='Program' else True)
            self.radClicked()
            self.radKaynak.toggled.connect(self.radClicked)
            self.cbxTekrarAcma.setChecked(True if self.ctx.tekraracma else False)
            self.spnTekrarEnGec.setValue(self.ctx.TekrarEnGec)
            self.btnKulSif.clicked.connect(self.ctx.kulAdSifAlAc)
            self.btnLogReset.clicked.connect(self.logReset)
            self.timMinSaat.setTime(QTime.fromString(self.ctx.minSaat))
            self.timMaxSaat.setTime(QTime.fromString(self.ctx.maxSaat))
            #ikinci tab
            self.spnSureArtim.setValue(self.ctx.SureArtim)
            self.cbxIcerikOto.setChecked(True if self.ctx.IcerikOto else False)
            self.cbxIcerikDS.setChecked(True if self.ctx.IcerikDS else False)
            self.cbxIcerikTum.setChecked(True if self.ctx.IcerikTum else False)
            self.FFMpeg=self.ctx.FFMpeg
            self.txtFFMpeg.setText(self.FFMpeg)
            #üçüncü tab
            self.txtSanalSrv.setText(self.ctx.SanalSrv)
            self.txtLmsSrv.setText(self.ctx.LmsSrv)
            #butonlar
            self.btnFFMpeg.clicked.connect(self.dosyaFFMpeg)
            self.buttonBox.accepted.connect(self.applyAll)
            self.buttonBox.rejected.connect(self.cancel)
            self.tabWidget.setCurrentIndex(0)
            self.exec_()
            debug = self.debug
            self.ctx.online = self.online

        def radClicked(self):
            if self.radKaynak.isChecked(): self.radKaynak.setText('Kaynak: Liste')
            else: self.radKaynak.setText('Kaynak: Program')

        def dosyaFFMpeg(self):
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            fileName, _ = QFileDialog.getOpenFileName(self, "Ayarlar - FFMPEG.exe Dosyası", self.ctx.FFMpeg ,"Executable Files (*.exe)")
            if fileName!='':
                self.FFMpeg = fileName
                self.txtFFMpeg.setText(self.FFMpeg)

        def logReset(self):
            if self.ctx.TimedMessageBox('Ayarlar',f'Log dosyası {logfile} içeriği silinecek, emin misiniz?',QMessageBox.Yes | QMessageBox.No , timeout=10, defaultBtn=QMessageBox.No, noExec=True).exec_()==QMessageBox.Yes:
                open(logfile,'w').close()
                if debug: print(f"Ayarlar: {logfile} içeriği silindi.")
            os.remove(anaKlasor + '\\oys-ders.html')
            os.remove(anaKlasor + '\\oys-meetings.xml')
            os.system(f"start {anaKlasor}")
            self.ctx.TimedMessageBox('Ayarlar', 'alt klasördeki dosyaları silebilirsiniz.', QMessageBox.Ok, 5)

        def cancel(self):
            if debug: print(f"Ayarlar: iptal edildi")

        def applyAll(self):
            self.ctx.dersDakika = self.spnDakika.value()
            self.ctx.ayarYaz('DersProgram', 'dersDakika', str(self.ctx.dersDakika))
            self.debug = self.cbxDebug.isChecked()
            #print('Ayarlar: debug=', 'Evet' if self.debug else 'Hayir')
            self.ctx.ayarYaz('Ayar', 'debug', 'Evet' if self.debug else 'Hayir')
            self.online = self.cbxOnline.isChecked()
            self.ctx.ayarYaz('Ayar', 'online', self.ctx.getOnline(self.online))
            self.ctx.main_window.lblOnOff.setText('(Online)' if self.online else '(Offline)')
            if debug: self.ctx.logYaz(f"Ayarlar: Online= {self.ctx.getOnline(self.online)}")
            self.ctx.minSaat = self.timMinSaat.time().toString('hh:mm')
            self.ctx.ayarYaz('DersProgram', 'minSaat', self.ctx.minSaat)
            self.ctx.maxSaat = self.timMaxSaat.time().toString('hh:mm')
            self.ctx.ayarYaz('DersProgram', 'maxSaat', self.ctx.maxSaat)
            self.ctx.TimerDk=self.spnTimerDk.value()
            self.ctx.ayarYaz('Ayar', 'TimerDk',str(self.ctx.TimerDk))
            self.ctx.GuncellemeDk=self.spnGuncellemeDk.value()
            self.ctx.ayarYaz('DersProgram', 'GuncellemeDk',str(self.ctx.GuncellemeDk))
            self.ctx.dpKaynak='Liste' if self.radKaynak.isChecked() else 'Program'
            self.ctx.ayarYaz('DersProgram', 'Kaynak', self.ctx.dpKaynak)
            self.ctx.tekraracma = self.cbxTekrarAcma.isChecked()
            self.ctx.ayarYaz('DersProgram', 'TekrarAcma', 'Evet' if self.ctx.tekraracma else 'Hayir')
            self.ctx.TekrarEnGec=self.spnTekrarEnGec.value()
            self.ctx.ayarYaz('DersProgram', 'TekrarEnGec',str(self.ctx.TekrarEnGec))
            self.ctx.SureArtim=self.spnSureArtim.value()
            self.ctx.ayarYaz('IcerikOkuma', 'SureArtim',str(self.ctx.SureArtim))
            self.ctx.IcerikOto = self.cbxIcerikOto.isChecked()
            self.ctx.ayarYaz('IcerikOkuma', 'OtomatikBasla', 'Evet' if self.ctx.IcerikOto else 'Hayir')
            self.ctx.IcerikDS = self.cbxIcerikDS.isChecked()
            self.ctx.ayarYaz('IcerikOkuma', 'SorulariOku', 'Evet' if self.ctx.IcerikDS else 'Hayir')
            self.ctx.IcerikTum = self.cbxIcerikTum.isChecked()
            self.ctx.ayarYaz('IcerikOkuma', 'TumunuOku', 'Evet' if self.ctx.IcerikTum else 'Hayir')
            self.ctx.FFMpeg = self.FFMpeg
            self.ctx.ayarYaz('Ayar', 'FFMpeg',self.ctx.FFMpeg)
            self.ctx.SanalSrv = self.txtSanalSrv.text()
            self.ctx.ayarYaz('Ayar', 'SanalSrv', self.ctx.SanalSrv)
            self.ctx.LmsSrv = self.txtLmsSrv.text()
            self.ctx.ayarYaz('Ayar', 'LmsSrv', self.ctx.LmsSrv)

    def ayarlariAc(self):
        self.ctx.Ayarlar(self.ctx)
        if debug: self.ctx.logYaz(f'ayarlariAc: Ayarlar açıldı/kapandı.')

#BAŞLANGIÇ AYARLARI

    def ayarlariOku(self):
        global debug
        os.makedirs(anaKlasor, exist_ok=True)
        if not os.path.isfile(logfile):
            with open(logfile, 'w') as dosya:
                dosya.write('Yeni Dosya')
                dosya.close()
        self.ctx.session=  None
        debug = self.ctx.ayarOku('Ayar', 'debug')
        if debug == 'Evet':
            debug = True  # konsola bilgi yaz
        else:
            debug = False
        self.ctx.ayarYaz('Ayar', 'debug', 'Evet' if debug else 'Hayir')
        self.ctx.setOnline (self.ctx.ayarOku('Ayar', 'online'))
        self.ctx.ayarYaz('Ayar', 'online', self.ctx.getOnline())
        self.ctx.dbConnected = False
        ayarDeger = self.ctx.ayarOku('Ayar', 'TimerDk')
        if ayarDeger is None: ayarDeger = '2' #1 dakikada bir kontrol
        self.ctx.TimerDk = int(ayarDeger)
        ayarDeger = self.ctx.ayarOku('DersProgram', 'GuncellemeDk')
        if ayarDeger is None: ayarDeger = '120' #ders programı online güncelleme için geçmesi gereken süre
        self.ctx.GuncellemeDk = int(ayarDeger)
        self.ctx.dpKaynak = self.ctx.ayarOku('DersProgram', 'Kaynak')
        if self.ctx.dpKaynak is None: self.ctx.dpKaynak='Program'
        ayarDeger = self.ctx.ayarOku('DersProgram', 'dersDakika')
        if ayarDeger is None: ayarDeger = '3' #dersten 3 dakika önce aç
        self.ctx.dersDakika = int(ayarDeger)
        self.ctx.minSaat = self.ctx.ayarOku('DersProgram', 'minSaat')
        if self.ctx.minSaat is None: self.ctx.minSaat = '17:30' #otomatik izleme en erken
        self.ctx.maxSaat = self.ctx.ayarOku('DersProgram', 'maxSaat')
        if self.ctx.maxSaat is None: self.ctx.maxSaat = '23:30' #otomatik izleme en geç
        self.ctx.tekraracma = True if self.ctx.ayarOku('DersProgram', 'TekrarAcma') == 'Evet' else False
        ayarDeger = self.ctx.ayarOku('DersProgram', 'TekrarEnGec')
        if ayarDeger is None: ayarDeger = '10' #dersten sonra tekrar açma en son sınır
        self.ctx.TekrarEnGec = int(ayarDeger)
        #tab 2 ayarları
        ayarDeger = self.ctx.ayarOku('IcerikOkuma', 'SureArtim')
        if ayarDeger is None: ayarDeger = 10 #icerik okuma süre artırım
        self.ctx.SureArtim = int(ayarDeger)
        self.ctx.IcerikOto = False if self.ctx.ayarOku('IcerikOkuma', 'OtomatikBasla') == 'Hayir' else True
        self.ctx.IcerikDS = False if self.ctx.ayarOku('IcerikOkuma', 'SorulariOku') == 'Hayir' else True
        self.ctx.IcerikTum = True if self.ctx.ayarOku('IcerikOkuma', 'TumunuOku') == 'Evet' else False
        ayarDeger = self.ctx.ayarOku('Ayar', 'FFMpeg')
        if ayarDeger is None: ayarDeger='D:\\pi\\util\\ffmpeg\\ffmpeg.exe'
        self.ctx.FFMpeg = ayarDeger
        ayarDeger = self.ctx.ayarOku('Ayar', 'SanalSrv')
        if ayarDeger is None: ayarDeger='sanal.yesevi.edu.tr'
        self.ctx.SanalSrv = ayarDeger
        ayarDeger = self.ctx.ayarOku('Ayar', 'LmsSrv')
        if ayarDeger is None: ayarDeger='lms.yesevi.edu.tr'
        self.ctx.LmsSrv = ayarDeger
        self.ctx.Mesaj = self.ctx.ayarOku('Login','Mesaj') #gelen mesaj sayısı, en son

#AYAR-LOG-ÇEREZ-RESPONSE DOSYA İŞLEMLERİ

    def ayarYaz(self, grup, ayar, deger):
        if 'Ayar' not in Config:
            Config['Ayar'] = {}
            Config['Ayar']['AyarOkundu'] = 'Hayır'
            if debug: self.ctx.logYaz('ayarYaz: Ayarlar dosyadan okunmamış!')
        else:
            Config['Ayar']['AyarOkundu'] = 'Evet'
        if grup not in Config:
            Config[grup] = {}
        Config[grup][ayar] = deger
        with open(ayarlar, 'w') as configfile:
            Config.write(configfile)
            configfile.close()
        return deger

    def ayarOku(self, grup, ayar):
        if 'Ayar' in Config:
            if grup in Config:
                if ayar in Config[grup]:
                    return Config[grup][ayar]
                else:
                    return None
            else:
                return None
        else:
            Config['Ayar'] = {}
            Config['Ayar']['AyarOkundu'] = 'Hayır'
            if Config.read(ayarlar) == []:
                if debug: self.ctx.logYaz('ayarOku: Ayarlar dosyası yok')
                self.ayarYaz('Ayar', 'AyarOkundu', 'YeniDosya')
                return None
            else:
                return self.ayarOku(grup, ayar)

    def logYaz(self, text):
        text = datetime.now().strftime("%d.%m.%Y") + '/' + datetime.now().strftime('%H:%M') + ': ' + text + '\n'
        text.encode('utf-8')
        with open(logfile, 'a') as dosya:
            dosya.write(text)
            dosya.close()

    def cerezYaz(self, cerezler):
        global cerezF
        self.ctx.cerezler = cerezler
        with open(cerezF, 'wb') as dosya:
            pickle.dump(cerezler, dosya)
            dosya.close()

    def cerezOku(self):
        global cerezF
        try:
            with open(cerezF, 'rb') as dosya:
                cerezler = pickle.load(dosya)
                dosya.close()
                self.ctx.cerezler = cerezler
        except:
            cerezler = None
        return cerezler

    def responseYaz(self, dosyaadi, icerik):
        with open(dosyaadi, 'w', encoding="utf-8") as dosya:
            if debug: self.ctx.logYaz(f'responseYaz: {dosyaadi} yazıldı')
            dosya.write(icerik)
            dosya.close()

    def responseOku(self, mydosya):
        with open(mydosya, 'r', encoding="utf-8") as dosya:
            yanit = dosya.read()
            dosya.close()
        return yanit


#VERİTABANI İŞLEMLERİ

    def dbConnect(self):
        if not self.ctx.dbConnected:
            self.ctx.db = sqlite3.connect(dbfile)
            self.ctx.dbConnected = True
        return self.ctx.db

    def dbCursor(self):
        return self.dbConnect().cursor()

    def dbTableExists(self, table):
        cursor = self.dbCursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        row = cursor.fetchone()
        if row is None:
            return False
        else:
            return True

#TARİH-SAAT İŞLEMLERİ

    def bugun(self):
        return datetime.now().strftime("%d.%m.%Y")

    def bugunmu(self, gun1):
        return gun1 == self.ctx.bugun()

    def bugunmuD(self,date1):
        return self.ctx.date2gun(date1) == self.ctx.bugun()

    def tarihfarki(self,tarih1,tarih2):
        return (self.ctx.gun2date(tarih1) - self.ctx.gun2date(tarih2)).days    #metin formatında 2 tarih arası fark, gün olarak

    def date2gun(self,tarih):
        return tarih.strftime('%d.%m.%Y')   #date formatından metin formatına

    def gun2date(self,gun):
        return datetime.strptime(gun,'%d.%m.%Y')   #metin formatından date formatına

    def kalanDakika(self, saat1):
        simdi = datetime.now().strftime('%H:%M')
        alt = datetime.strptime(simdi, '%H:%M')
        ust = datetime.strptime(saat1, '%H:%M')
        if ust < alt:
            kalan = -1 * self.ctx.gecenDakika(saat1)
        else:
            kalan = int((ust - alt).seconds / 60)
        if debug: self.ctx.logYaz(
            f"===kalanDakika: {kalan} dk. saat1={saat1} şimdi={simdi} <-{sys._getframe().f_back.f_code.co_name}")
        return kalan

    def gecenDakika(self, saat1, tarih=None, limitDakika=None, limitDisi=False):
        simdi = datetime.now().strftime('%H:%M')
        bugun = self.ctx.bugun()
        ust = datetime.strptime(simdi, '%H:%M')
        alt = datetime.strptime(saat1, '%H:%M')
        if tarih is None: tarih = self.ctx.bugun()
        gecengun = self.ctx.tarihfarki(tarih, bugun)
        ust = ust + timedelta(minutes = 1440 * gecengun)
        gecen = int((ust - alt).seconds / 60)
        if debug: self.ctx.logYaz(
            f"===gecenDakika: {gecen} dk. saat1={saat1} şimdi={simdi} <-{sys._getframe().f_back.f_code.co_name}")
        if limitDakika is not None:
            if limitDisi:
                return True if gecen >= 0 and gecen >= limitDakika else False
            else:
                return True if gecen >= 0 and gecen <= limitDakika else False
        else:
            return gecen

    def kulAdSifAlAc(self):
        self.ctx.KulAdSifAl(self.ctx)

    class KulAdSifAl(QDialog):
        @pyqtSlot()
        def btn_Login_clicked(self):
            self.ctx.ayarYaz('Kullanici', 'kullanici_adi', self.txt_KulAd.text())
            if debug: self.ctx.logYaz(f'kuad_sif_al:{self.txt_KulAd.text()}')
            self.ctx.ayarYaz('Kullanici', 'sifre',
                             str(base64.b64encode(self.txt_KulSif.text().encode()).decode('utf-8')))
            self.close()

        def __init__(self, ctx):
            super(QDialog, self).__init__()
            self.ctx = ctx
            dlayout = QVBoxLayout(self)
            # kullanici=self.ctx.initKullanici()
            kullanici = self.ctx.ayarLogin()
            lbl_KulAd = QLabel('Kullanıcı adı (TC No):', self)
            dlayout.addWidget(lbl_KulAd)
            self.txt_KulAd = QLineEdit(self)
            dlayout.addWidget(self.txt_KulAd)
            self.txt_KulAd.setText(kullanici['kullanici_adi'])
            lbl_KulSif = QLabel('Şifre:', self)
            dlayout.addWidget(lbl_KulSif)
            self.txt_KulSif = QLineEdit(self)
            self.txt_KulSif.setEchoMode(QLineEdit.Password)
            dlayout.addWidget(self.txt_KulSif)
            # self.txt_KulSif.setText(kullanici['sifre'].decode('utf-8'))
            self.txt_KulSif.setText(kullanici['sifre'])
            btn_Login = QPushButton('Login', self)
            btn_Login.clicked.connect(self.btn_Login_clicked)
            dlayout.addWidget(btn_Login)
            self.setWindowModality(Qt.ApplicationModal)
            self.setLayout(dlayout)
            self.setGeometry(0, 0, 150, 150)
            self.exec()

    class TimedMessageBox(QMessageBox):
        def __init__(self, title, text, buttons=QMessageBox.Ok, timeout=3, defaultBtn=None, noExec=False):
            super(QMessageBox, self).__init__()
            self.setWindowTitle(title)
            self.setText(text)
            self.setStandardButtons(buttons)
            if defaultBtn: self.setDefaultButton(defaultBtn)
            self.timer = QTimer()
            self.timer.setInterval(timeout * 1000)
            self.timer.timeout.connect(self.autoClose)
            self.timer.start()
            if not noExec: self.exec_()

        def autoClose(self):
            self.timer.stop()
            self.close()

#OTURUM-SESSİON LOGON İŞLEMLERİ

    def initKullanici(self):
        kullanici = {
            'giris_yap_btn': 'Sisteme Giriş Yap',
            'kullanici_adi': '',
            'sifre': '',
            'sg': '',
            'deger_adi': ''
        }
        return kullanici

    def ayarLogin(self):
        kullanici = self.initKullanici()
        if self.ayarOku('Kullanici', 'kullanici_adi') is None or self.ayarOku('Kullanici', 'sifre') is None:
            if debug: self.ctx.logYaz('ayarLogin:' + 'Kullanıcı Adı/Şifre boş!')
            # self.ctx.KulAdSifAl(self.ctx)
        else:
            kullanici['kullanici_adi'] = self.ayarOku('Kullanici', 'kullanici_adi')
            kullanici['sifre'] = base64.b64decode(bytearray(self.ayarOku('Kullanici', 'sifre'), 'utf-8')).decode(
                'utf-8')
        # if debug: QMessageBox.question(self.main_window, 'Ayar yap', 'Ayarlar Okundu', QMessageBox.Ok)
        if debug: self.ctx.TimedMessageBox('ayarLogin', 'Kullanıcı adı/şifre Okundu', QMessageBox.Ok, 3)
        return kullanici

    def getSession(self):
        if self.ctx.session is None: self.ctx.session=requests.session()
        if debug: print(f"getSession: {self.ctx.session} <- {sys._getframe().f_back.f_code.co_name}")
        return self.ctx.session

    def loginKontrol(self):
        cerezler = self.cerezOku()
        try:
            if self.ctx.online:
                yanit = self.ctx.getSession().get(adres + '/mesajlar', cookies=cerezler)
                yanit.encoding = 'UTF-8'
                sayfa = yanit.text
                self.responseYaz(anaKlasor + '\\oys-mesaj.html', sayfa)
                durum = yanit.status_code
            else:
                with open(anaKlasor + '\\oys-mesaj.html', 'r', encoding="utf-8") as dosya:
                    durum = 'Offline <200>'
                    sayfa = dosya.read()
                    dosya.close()
            soup = BeautifulSoup(sayfa, features='html.parser')
            if soup.find('div', {'class': 'alert alert-danger'}):
                if debug: self.ctx.logYaz("loginKontrol: Kullanıcı/Şifre hatalı!!! ")
                self.main_window.btn_Login.setVisible(True)
                self.ctx.loggedIn = False
                kullanici_adi = None
            if soup.find('span', {'class': 'username username-hide-on-mobile'}):
                kullanici_adi = soup.find('span', {'class': 'username username-hide-on-mobile'}).text
                self.ayarYaz('Login', 'kullanici_adi', kullanici_adi)
                self.ctx.loggedIn = True
                self.main_window.btn_Login.setVisible(False)
                if debug: self.ctx.logYaz(f'loginKontrol: kullanici_adi={kullanici_adi} status={durum}')
            else:
                if debug: self.ctx.logYaz('loginKontrol: kullanici_adi bulunamadı! Giriş yapın.')
                self.main_window.btn_Login.setVisible(True)
                self.ctx.loggedIn = False
                kullanici_adi = None
        except requests.exceptions.RequestException as e:
            if debug: self.ctx.logYaz(f'loginKontrol: HATA e={e}')
            self.main_window.btn_Login.setVisible(True)
            self.ctx.loggedIn = False
            kullanici_adi = self.login()
        except requests.HTTPError as e:
            if debug: self.ctx.logYaz(f'loginKontrol: HATA e={e}')
            self.main_window.btn_Login.setVisible(True)
            self.ctx.loggedIn = False
            kullanici_adi = self.login()
        return kullanici_adi

    def login(self):
        kullanici = self.ayarLogin()
        if self.ctx.online:
            yanit = self.ctx.getSession().get(adres)
            yanit.encoding = 'UTF-8'
            sayfa = yanit.text
            self.responseYaz(anaKlasor + '\\oys-ana.html', sayfa)
        else:
            with open(anaKlasor + '\\oys-ana.html', 'r', encoding="utf-8") as dosya:
                sayfa = dosya.read()
                dosya.close()
        soup = BeautifulSoup(sayfa, features='html.parser')
        Inputs = soup.find_all('input', {'type': 'hidden'})
        if debug: print('login: Inputs=', Inputs)  # bulunan tüm gizli Input tagler. bunlar login paketi oluşturmak için
        for gizli in Inputs:
            # if debug: self.ctx.logYaz('login:' + gizli)
            if gizli.attrs['name'] == 'sg':
                kullanici['sg'] = gizli.attrs['value']
            if 'id' in gizli.attrs and gizli.attrs['id'] == 'cb':
                kullanici['deger_adi'] = gizli.attrs['name']
                kullanici[gizli.attrs['name']] = ''
            if gizli.attrs['name'] == 'pd':
                kullanici[kullanici['deger_adi']] = gizli.attrs['value']
        # if debug: self.ctx.logYaz(f'login: kullanici={kullanici}') #şifreyi açık gösteriyor, gerekmezse kaldır
        if self.ctx.online:
            yanit = self.ctx.getSession().post(adres + '/login', data=kullanici)
            yanit.encoding = 'UTF-8'
            sayfa = yanit.text
            self.responseYaz(anaKlasor + '\\oys-login.html', sayfa)
            # if debug: print('login: sayfa=', sayfa)
            cerezler = yanit.cookies
        else:
            with open(anaKlasor + '\\oys-login.html', 'r', encoding="utf-8") as dosya:
                sayfa = dosya.read()
                dosya.close()
                cerezler = self.cerezOku()
        if debug: print('login: çerezler=', cerezler)
        if debug: self.ctx.logYaz(f'login: type-cerezler={str(type(cerezler))}')
        self.cerezYaz(cerezler)
        self.ctx.loggedIn = False
        soup = BeautifulSoup(sayfa, features='html.parser')
        if soup.find('div', {'class': 'alert alert-danger'}):
            if debug: self.ctx.logYaz("login: Kullanıcı/Şifre hatalı!!!")
            self.main_window.btn_Login.setVisible(True)
            return None
        if soup.find('span', {'class': 'username username-hide-on-mobile'}):
            kullanici_adi = soup.find('span', {'class': 'username username-hide-on-mobile'}).text
            self.ayarYaz('Login', 'kullanici_adi', kullanici_adi)
            if debug: self.ctx.logYaz(f"login: kullanici_adi={kullanici_adi}")
            self.main_window.btn_Login.setVisible(False)
            self.ctx.loggedIn = True
        else:
            kullanici_adi = None
            if debug: self.ctx.logYaz(f"login: Kullanıcı/Şifre hatalı? kullanici_adi={kullanici_adi}")
            self.main_window.btn_Login.setVisible(True)
        return kullanici_adi

    def onlineOl(self):
        if self.ctx.onlineOldu:
            if int((self.onlinesaat - datetime.now()).seconds) < (ONLINESURE * 60):
                user_id, login, name, self.ctx.cerezler = self.getCommonInfo(self.oturum, self.ctx.session)
                return self.oturum
        self.ctx.online = True
        if self.ctx.loginKontrol() is None:
            if not self.ctx.login():
                return None
        self.ctx.cerezler = self.ctx.cerezOku()
        self.oturum = self.oturumGetir(self.ctx.cerezler, mesajGetir=False)
        user_id, login, name, self.ctx.cerezler = self.getCommonInfo(self.oturum, self.ctx.session)
        self.ctx.cerezler['BREEZESESSION'] = self.oturum
        if debug: print(f"onlineOl: user_id={user_id} name={name} login={login} oturum={self.oturum} cerezler={self.ctx.cerezler}")
        self.onlinesaat= datetime.now()
        self.ctx.onlineOldu= True
        return self.oturum

    def getCommonInfo(self, oturum, session=None):
        cerezler = self.ctx.cerezOku()
        cerezler['BREEZESESSION'] = oturum
        if session is None:
            yanit = requests.get(f'http://{self.ctx.SanalSrv}/api/xml?action=common-info', cookies=cerezler)
        else:
            yanit = session.get(f'http://{self.ctx.SanalSrv}/api/xml?action=common-info', cookies=cerezler)
        yenicerez= yanit.cookies
        yanit.encoding = 'UTF-8'
        yenicerez['BREEZESESSION'] = oturum
        if 'BreezeCCookie' in yenicerez:
            cerezler['BreezeCCookie'] = yenicerez['BreezeCCookie']
        self.ctx.cerezYaz(cerezler)
        soup = BeautifulSoup(yanit.text, 'lxml')
        name = soup.find('name')
        if name: name = name.text
        login = soup.find('login')
        if login: login = login.text
        user = soup.find('user')
        if user is not None:
            user_id = user['user-id']
        else:
            user_id = None
        return user_id, login, name, yenicerez

    def oturumGetir(self, cerezler, mesajGetir=True):
        if mesajGetir:
            veri = {'page': 'get-badge-data', 'sg': ''}
            yanit = self.ctx.getSession().post(adres + '/getMessagePage', data=veri, cookies=cerezler)
            yanit.encoding = 'UTF-8'
            sonuc = yanit.json()
            mesaj = eval(sonuc['Deger'])
            if debug: self.ctx.logYaz(f"oturumGetir: Gelen Mesaj Sayısı={mesaj['GELEN']}, Giden Mesaj={mesaj['GIDEN']}")
            if mesaj['GELEN'] > 0:
                self.ctx.main_window.lblMesaj.setText(f"Mesaj: {mesaj['GELEN']}")
                self.ctx.TimedMessageBox("oturumGetir", f"Mesajınız Var ({mesaj['GELEN']})")
            else:
                self.ctx.main_window.lblMesaj.setText(f"Mesaj: {0}")
            self.ctx.ayarYaz('Login', 'Mesaj', str(mesaj['GELEN']))
        veri = {'page': 'GTACSI', 'sg': ''}
        yanit = self.ctx.getSession().post(adres + '/getMessagePage', data=veri, cookies=cerezler)
        yanit.encoding = 'UTF-8'
        sonuc = yanit.json()
        oturum = sonuc['Deger']
        if debug: print(f'oturumGetir: session={oturum}')
        self.ctx.ayarYaz('Login', 'oturum', oturum)
        self.ctx.oturum = oturum
        return oturum


class AnaPencere(QMainWindow):
    def __init__(self, ctx):
        super(AnaPencere, self).__init__()
        self.ctx = ctx
        self.ctx.ayarlariOku()
        version = self.ctx.build_settings['version']
        self.title = 'OYS-Yesevi otomatik ders izleme v' + version
        self.setWindowTitle(self.title)
        self.resize(280, 150)
        kullanici_adi = self.ctx.ayarOku('Login', 'kullanici_adi')
        self.anaform = QWidget(self)
        self.anaVLayout = QVBoxLayout(self.anaform)
        self.anaLayout = QHBoxLayout(self.anaform)
        self.anaVLayout.addLayout(self.anaLayout)
        # self.anaform.setLayout(self.anaLayout)
        self.setCentralWidget(self.anaform)
        self.lblOnOff = QLabel('(Online)' if self.ctx.online else '(Offline)', self.anaform)
        self.anaLayout.addWidget(self.lblOnOff)
        self.anaLayout.addWidget(QLabel('Kullanıcı Adı:', self.anaform))
        self.lbl_KullaniciAd = QLabel(kullanici_adi, self.anaform)
        self.anaLayout.addWidget(self.lbl_KullaniciAd)
        self.btn_Login = QPushButton('Login', self)
        self.btn_Login.clicked.connect(self.btnLoginClicked)
        self.anaLayout.addWidget(self.btn_Login)
        self.lblMesaj=QLabel(f"Mesaj: {self.ctx.Mesaj}", self.anaform)
        self.anaVLayout.addWidget(self.lblMesaj)
        if kullanici_adi != None and kullanici_adi.strip() != '':
            self.lbl_KullaniciAd.setText(kullanici_adi)
            self.btn_Login.hide()
            self.ctx.loggedIn = True
        else:
            self.btn_Login.show()
            self.ctx.loggedIn = False
        self.setupMenu()
        self.show()

    @pyqtSlot()
    def btnLoginClicked(self):
        kullanici_adi = self.ctx.login()
        self.lbl_KullaniciAd.setText(kullanici_adi)
        # self.anaLayout.removeWidget(self.btn_Login)
        if kullanici_adi is not None:
            self.btn_Login.setVisible(False)
        else:
            self.btn_Login.setVisible(True)
        if debug: self.ctx.logYaz(f'btnLoginClicked: kullanici_adi={kullanici_adi}')

    @pyqtSlot()
    def closeEvent(self, e):
        if debug: self.ctx.logYaz(f'Uygulama kapatıldı...')
        e.accept()
        #self.deleteLater()

    @pyqtSlot()
    def dersProgramiAc(self):
        b = dersProgrami(self.ctx)
        # b.show()

    @pyqtSlot()
    def scogezginiac(self):
        self.ctx.anaKlasor = anaKlasor
        self.ctx.debug = debug
        # self.ctx.getCommonInfo=dersProgrami.getCommonInfo
        # self.ctx.oturumGetir=dersProgrami.oturumGetir
        b = scoGezgini(self.ctx)

    @pyqtSlot()
    def dersIcerikAc(self):
        self.ctx.anaKlasor = anaKlasor
        self.ctx.debug = debug
        self.ctx.adres = adres
        b = dersIcerik(self.ctx)

    @pyqtSlot()
    def dersArsivAc(self):
        self.ctx.anaKlasor = anaKlasor
        self.ctx.debug = debug
        self.ctx.adres = adres
        b = dersArsiv(self.ctx)

    def setupMenu(self):
        menu = self.menuBar().addMenu("&Dosya")
        #ders programı menüsü
        dersProgramiM = QAction('&Ders Programı ve İzleme', self)
        dersProgramiM.triggered.connect(self.dersProgramiAc)
        menu.addAction(dersProgramiM)
        #sco gezgini menüsü
        scoGezginiM=QAction('&SCO Gezgini', self)
        scoGezginiM.triggered.connect(self.scogezginiac)
        menu.addAction(scoGezginiM)
        #içerik okuma
        dersIcerikM=QAction('Ders İçeri&kleri', self)
        dersIcerikM.triggered.connect(self.dersIcerikAc)
        menu.addAction(dersIcerikM)
        #arşiv izleme
        dersArsivM=QAction('Arşiv İ&zleme', self)
        dersArsivM.triggered.connect(self.dersArsivAc)
        menu.addAction(dersArsivM)
        # ayar menüsü
        ayarlari_ac = QAction('&Ayarlar', self)
        ayarlari_ac.triggered.connect(self.ctx.ayarlariAc)
        menu.addAction(ayarlari_ac)
        # çıkış menüsü
        close_action = QAction('&Çıkış', self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)
        # help menüsü
        help_menu = self.menuBar().addMenu("&Yardım")
        about_action = QAction('&Hakkında', self)
        help_menu.addAction(about_action)

        def show_about_dialog(menu):
            text = "<center>" \
                   "<h1>Yesevi Otomatik Ders İzleme</h1>" \
                   "&#8291;" \
                   "</center>" \
                   "<p>Version " + self.ctx.build_settings['version'] + "<br/>" \
                                                                        "Copyright &copy; pi511</p>"
            QMessageBox.about(self, "OYS Otomatik Ders İzleme Hakkında", text)

        about_action.triggered.connect(show_about_dialog)


class dersProgrami(QDialog):
    def __init__(self, ctx):
        super(dersProgrami, self).__init__()
        self.ctx = ctx
        self.title = 'Ders Programı'
        self.otomatik = False  # otomatik ders izleme kapalı
        self.initUI()
        if self.ders_programi_getir():
            self.dersProgramDoldur()
            self.exec()
        else:
            self.reject()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.tableWidget = QTableWidget()
        self.ctx.dersSayisi=6
        self.tableWidget.setRowCount(self.ctx.dersSayisi)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(['Ders Adı', 'Tarih', 'Saat', 'Kalan Süre', 'Bağlantı'])
        self.tableWidget.setColumnWidth(0, 400)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.setColumnWidth(2, 50)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setColumnWidth(4, 250)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.btn_Baslat = QPushButton('Otomatik İzlemeyi Başlat', self)
        self.btn_Baslat.clicked.connect(self.btn_Baslat_clicked)
        self.layout.addWidget(self.btn_Baslat)
        self.setLayout(self.layout)
        self.setGeometry(50, 50, 1000, 300)

    def dersProgramDoldur(self):
        dersler = self.ders_program_kontrol()
        if len(dersler) != self.ctx.dersSayisi:
            self.ctx.dersSayisi = len(dersler)
            self.tableWidget.setRowCount(self.ctx.dersSayisi)
        i = 0
        for ders in dersler:
            self.tableWidget.setItem(i, 0, QTableWidgetItem(ders['ders']))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(ders['tarih']))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(ders['saat']))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(ders['kalan'] + ' dakika'))
            self.tableWidget.setItem(i, 4, QTableWidgetItem(ders['link']))
            # self.tableWidget.setItem(i, 4, QTableWidgetItem('<a href="' + ders['link'] + '">' + ders['link'] + '</a>'))
            i += 1
        if ilkders > -1:
            if self.otomatik:
                self.tableWidget.item(ilkders, 2).setBackground(Qt.green)
            else:
                self.tableWidget.item(ilkders, 2).setBackground(Qt.white)
        if debug: self.ctx.logYaz(f'dersProgramDoldur: {i} ders dolduruldu, ilkders={ilkders}')

    @pyqtSlot()
    def closeEvent(self, event):
        if self.otomatik:
            self.otomatik = False
            if debug: print(f"Otomatik izleme kapandı")
            self.ders_zamanla(False)

    @pyqtSlot()
    def btn_Baslat_clicked(self):
        global ilkders, dersler
        if self.otomatik:
            self.btn_Baslat.setText('Otomatik İzlemeyi Başlat')
            self.otomatik = False
            self.ders_zamanla(False)
            if debug: print(f"Otomatik İzleme kapalı")
            self.dersProgramDoldur()
        else:
            self.btn_Baslat.setText('Otomatik İzlemeyi İptal Et')
            self.otomatik = True
            self.ders_zamanla(True)
            if ilkders > -1:
                if debug: self.ctx.logYaz(f"Baslat_clicked: kalan={dersler[ilkders]['kalan']} dakika")
                self.dakikadaBir()
            else:
                if debug: self.ctx.logYaz(f"Başlat_clicked: Bu hafta ders yok!, ilkders={ilkders}")
        self.ctx.ayarYaz('DersProgram', 'Otomatik', 'Evet' if self.otomatik else 'Hayır')

    def ders_programi_getir(self):
        global dersler
        dersler = []
        if self.ctx.online:
            if self.ctx.onlineOl() is None:
                if debug: self.ctx.logYaz("dersProgramiGetir: Giriş Yapılmadı, iptal?")
                return None
            cerezler = self.ctx.cerezOku()
            yanit = self.ctx.getSession().post(adres + '/ders_islemleri_ekran', cookies=cerezler)
            yanit.encoding = 'UTF-8'
            sayfa = yanit.text
            self.ctx.responseYaz(anaKlasor + '\\oys-ders.html', sayfa)
            oturum = self.ctx.oturumGetir(cerezler)
        else:
            with open(anaKlasor + '\\oys-ders.html', 'r', encoding="utf-8") as dosya:
                sayfa = dosya.read()
                dosya.close()
            oturum = self.ctx.ayarOku('Login', 'oturum')
        soup = BeautifulSoup(sayfa, features='html.parser')
        if self.ctx.dpKaynak == 'Liste':
            liste = soup.find('div', {'class': 'col-md-12 tab-pane active','id':'contentHaftalikDers'})
            bulunandersler = liste.find_all('div', {'class': 'card hover make-it-slow card-items'})
            i = 0
            for bulunanders in bulunandersler:
                eleman = bulunanders.find('button', {'class': 'btn btn-outline-purple'})
                dersler.append({'ders': eleman['dersadi']})
                eleman = bulunanders.find('button', {'class': 'btn btn-outline-blue lesson-live'})
                if eleman:
                    dersler[i]['link'] = eleman['data-link']
                else:
                    dersler[i]['link'] = 'no-link'
                eleman = bulunanders.find('span', {'class': 'title-date'})
                if eleman:
                    dersler[i]['tarih'] = eleman.text
                else:
                    dersler[i]['tarih'] = 'Oturum yok'
                eleman = bulunanders.find('span', {'class': 'title-time'})
                if eleman:
                    dersler[i]['saat'] = eleman.text
                else:
                    dersler[i]['saat'] = '00:00'
                dersler[i]['acilsin'] = False
                if debug: self.ctx.logYaz(f"dersProgramiGetir:{i} {dersler[i]}")
                i += 1
        else:
            gunler = soup.find_all('li', {'class': 'events-group'})
            i = 0
            for gun in gunler:
                bulunandersler = gun.find_all('li', {'class': 'single-event'})
                tarih = gun.find('span').text[:5]+datetime.now().strftime('.%Y')
                for bulunanders in bulunandersler:
                    dersler.append({'saat': bulunanders['data-start']})
                    dersler[i]['tarih'] = tarih
                    eleman = bulunanders.find('span')
                    dersler[i]['ders'] = eleman.text
                    eleman = bulunanders.find('a', {'class': 'link_a btn green'})
                    if eleman:
                        dersler[i]['link']=eleman['onclick'].split("'")[1]
                    else:
                        dersler[i]['link'] = 'no-link'
                    dersler[i]['acilsin'] = False
                    if debug: self.ctx.logYaz(f"dersProgramiGetir:{i} {dersler[i]}")
                    i += 1
        Inputs = soup.find_all('input', {'type': 'hidden'})
        for gizli in Inputs:
            if 'id' in gizli.attrs and gizli.attrs['id'] == 'ACSI':
                # oturum = gizli.attrs['value']
                # self.ctx.ayarYaz('Login', 'oturum',oturum)
                if debug: self.ctx.logYaz(f'dersProgramiGetir: session={oturum}')
        self.ctx.ayarYaz('DersProgram', 'tarih', self.ctx.bugun())
        self.ctx.ayarYaz('DersProgram', 'saat', datetime.now().strftime('%H:%M'))
        return oturum

    def dersAraliktami(self, saat1):
        aralikta = False
        kalan=self.ctx.kalanDakika(saat1)
        engec = self.ctx.TimerDk if self.ctx.tekraracma else self.ctx.TekrarEnGec
        aralikli= kalan + engec
        if (kalan >= 0 and kalan <= self.ctx.dersDakika) or (kalan < 0 and kalan <= engec):
            aralikta=True
        return kalan, aralikli, aralikta

    def gecerliSaatler(self, saat1):
        gecerli = False
        sgn = '-----'
        if datetime.strptime(saat1, '%H:%M') >= datetime.strptime(self.ctx.minSaat, '%H:%M') and datetime.strptime(
                saat1, '%H:%M') <= datetime.strptime(self.ctx.maxSaat, '%H:%M'):
            gecerli = True
            sgn = '====='
        if debug: self.ctx.logYaz(f"{sgn}gecerliSaatler: min={self.ctx.minSaat} max={self.ctx.maxSaat} Şimdi={saat1}{sgn}")
        return gecerli

    def ders_program_kontrol(self):
        global ilkders, dersler
        bugunku = 1440
        ilkders=-1
        for i in range(len(dersler)):
            aralik = -1
            acilsin = False
            dersler[i]['acilsin'] = acilsin
            if self.ctx.bugunmu(dersler[i]['tarih']):
                kalan, aralik, acilsin = self.dersAraliktami(dersler[i]['saat'])
                dersler[i]['kalan'] = str(kalan)
                if aralik >= 0:
                    if aralik < bugunku:
                        bugunku = aralik
                        ilkders = i
                        dersler[i]['acilsin'] = acilsin
            else:
                dersler[i]['kalan'] = '0'
            if debug: print(f"ders_program_kontrol: i={i} ilkders={ilkders:+1d} aralikta mi={'Evet' if acilsin else 'Hayır'} aralık={aralik:+4d} bugunku={bugunku:+5d}", dersler[i])
        if debug: self.ctx.logYaz(f"ders_program_kontrol: ilkders={ilkders} aralikta {'' if acilsin else 'değil'}")
        return dersler

    def ders_program_guncelle(self):
        saat1 = self.ctx.ayarOku('DersProgram', 'saat')
        tarih = self.ctx.ayarOku('DersProgram', 'tarih')
        if self.ctx.gecenDakika(saat1, tarih = tarih, limitDakika = self.ctx.GuncellemeDk, limitDisi=True):
            if debug: self.ctx.logYaz(f"ders_program_guncelle: önceki güncelleme={saat1} periyod={self.ctx.GuncellemeDk}")
            self.ders_programi_getir()
        self.dersProgramDoldur()

    def dersAc(self, i):
        global dersler
        son = self.ctx.ayarOku('DersProgram', 'SonAcilan')
        simdiki = dersler[i]['tarih'] + '/' + dersler[i]['saat']
        if son != simdiki or (son == simdiki and not self.ctx.tekraracma):
            oturum = self.ders_programi_getir()
            dersurl = dersler[i]['link'] + '?session=' + oturum + '&proto=true'
            #webbrowser.open(f'http://{self.ctx.SanalSrv}/login?session=' + oturum)
            webbrowser.open(dersurl)
            user_id, login, name, yenicerez = self.ctx.getCommonInfo(oturum)
            #flvView(self.ctx,dersler[i]['link'] + '?session=' + oturum + '&proto=true')
            if debug: self.ctx.logYaz(dersurl)
            self.ctx.ayarYaz('DersProgram', 'SonAcilan', simdiki)
            if debug: self.ctx.logYaz(f"DersAc:{dersler[i]['link']} açıldı, Tekrar {'açılmayacak' if self.ctx.tekraracma else 'açılabilir'} ogrno={login} user-id={user_id}")
        else:
            if debug: self.ctx.logYaz(f"DersAc:{dersler[i]['link']} daha önce açılmış, TekrarEnGec={self.ctx.TekrarEnGec}")

    def ders_zamanla(self, baslat=True):
        if baslat:
            self.timer = QTimer()
            self.timer.timeout.connect(self.dakikadaBir)
            self.timer.start(60 * 1000 * self.ctx.TimerDk)
            if debug: self.ctx.logYaz(f"ders_zamanla: zamanlama başladı, {self.ctx.TimerDk} dk.da bir, ilkders={ilkders}")
        else:
            if debug: self.ctx.logYaz(f"ders_zamanla: zamanlama iptal edildi, ilkders={ilkders}")
            # self.timer.cancel()
            self.timer.stop()
            self.timer = None

    def dakikadaBir(self):
        global dersler, ilkders
        i = ilkders
        if self.gecerliSaatler(datetime.now().strftime('%H:%M')):
            self.ders_program_guncelle()
            if debug: self.ctx.logYaz(f"dakikadaBir: ders={i} {'açılacak' if dersler[i]['acilsin'] else 'açılmayacak'} tekrar kontrol={self.ctx.TimerDk} dk sonra")
            if i > -1 and self.ctx.bugunmu( dersler[i]['tarih'] ) and dersler[i]['acilsin']:
                self.dersAc(i)
                dersler[i]['acilsin'] = False
        else: self.dersProgramDoldur()


if __name__ == '__main__':
    appctxt = AppContext()  # 4. Instantiate the subclass
    exit_code = appctxt.run()  # 5. Invoke run()
    sys.exit(exit_code)


#INFO: http://sanal.yesevi.edu.tr/api/xml?action=common-info   breezesession almanın tavsiye edilen yolu, getCommonInfo
#INFO FBS komutlarını doğrudan fbs ile değil python -m fbs ile çalıştırın
#TODO açılan pencereye process listten bakıp, dersten 90 dakika sonra hala açık olan connect penceresini kapatma
#TODO yeni ödev ve ödev notu bildirimi (gereksiz)
#TODO dilekçe cevaplandı bildirimi (gereksiz)
#TODO mesajları progarm içinden okuma (gereksiz)
#TODO Dosyalara yeni dosya eklendi bildirimi, tüm dosyaları indirme (gereksiz)
#TODO sınav notlarını bir pencerede göserme (gereksiz)
#INFO D:\pi\work\python\yesevi-oys\Lib\site-packages\docx klasörünü D:\pi\work\python\yesevi-oys\target\oys-yesevi içine kopyala...