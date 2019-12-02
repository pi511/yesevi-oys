# coding=utf-8
from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
import base64
import sys, os
import webbrowser
from datetime import datetime
import configparser
import pickle
import requests
import requests.cookies
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSlot
#from PyQt5.QtWidgets import *
from bs4 import BeautifulSoup
from sco import *

online = True
debug = False
anaKlasor = 'c:\\pi\\temp'
ayarlar = anaKlasor + '\\oys-yesevi.ini'
cerezF = anaKlasor + '\\oys-yesevi-c.ini'
logfile = anaKlasor + '\\oys-yesevi.log'
Config = configparser.ConfigParser()
adres = 'https://oys.yesevi.edu.tr'
dersler = []
ilkders = -1


class AppContext(ApplicationContext):
    def __init__(self):
        super(AppContext, self).__init__()
        #global değişkenleri buraya alabilirsin

    def run(self):
        self.ctx = appctxt
        self.main_window.show()
        return self.app.exec_()

    @cached_property
    def main_window(self):
        self.app.setApplicationName('OYS')
        return AnaPencere(self)

    class Ayarlar(QDialog):
        def __init__(self, ctx):
            global online, debug
            super(QDialog, self).__init__()
            self.ctx = ctx
            # uic.loadUi('Ayarlar.ui',self)
            uic.loadUi(self.ctx.get_resource('Ayarlar.ui'), self)
            self.debug = debug
            self.online = online
            self.dersDakika = self.ctx.dersDakika
            self.spnDakika.setValue(self.ctx.dersDakika)
            self.cbxDebug.setChecked(debug)
            self.cbxOnline.setChecked(online)
            self.minSaat = self.ctx.minSaat
            self.maxSaat = self.ctx.maxSaat
            self.spnTimerDk.setValue(self.ctx.TimerDk)
            self.spnGuncellemeDk.setValue(self.ctx.GuncellemeDk)
            self.radKaynak.setChecked(False if self.ctx.dpKaynak=='Program' else True)
            self.radKaynak.toggled.connect(self.radClicked)
            self.cbxTekrarAcma.setChecked(True if self.ctx.tekraracma else False)
            self.spnTekrarEnGec.setValue(self.ctx.TekrarEnGec)
            self.btnKulSif.clicked.connect(self.ctx.kulAdSifAlAc)
            self.btnLogReset.clicked.connect(self.logReset)
            self.timMinSaat.setTime(QTime.fromString(self.ctx.minSaat))
            self.timMaxSaat.setTime(QTime.fromString(self.ctx.maxSaat))
            self.buttonBox.accepted.connect(self.applyAll)
            self.buttonBox.rejected.connect(self.cancel)
            self.exec_()
            debug = self.debug
            online = self.online

        def radClicked(self):
            if self.radKaynak.isChecked(): self.radKaynak.setText('Kaynak: Liste')
            else: self.radKaynak.setText('Kaynak: Program')

        def logReset(self):
            if self.ctx.TimedMessageBox('Ayarlar',f'Log dosyası {logfile} içeriği silinecek, emin misiniz?',QMessageBox.Yes | QMessageBox.No , timeout=10, defaultBtn=QMessageBox.No, noExec=True).exec_()==QMessageBox.Yes:
                open(logfile,'w').close()
                if debug: print(f"Ayarlar: {logfile} içeriği silindi.")

        def cancel(self):
            if debug: print(f"Ayarlar: iptal edildi")

        def applyAll(self):
            self.ctx.dersDakika = self.spnDakika.value()
            self.ctx.ayarYaz('DersProgram', 'dersDakika', str(self.ctx.dersDakika))
            self.debug = self.cbxDebug.isChecked()
            #print('Ayarlar: debug=', 'Evet' if self.debug else 'Hayir')
            self.ctx.ayarYaz('Ayar', 'debug', 'Evet' if self.debug else 'Hayir')
            self.online = self.cbxOnline.isChecked()
            self.ctx.ayarYaz('Ayar', 'online', 'Evet' if self.online else 'Hayir')
            self.ctx.main_window.lblOnOff.setText('(Online)' if self.online else '(Offline)')
            if debug: self.ctx.logYaz(f"Ayarlar: Online= {'Evet' if self.online else 'Hayir'}")
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

    def ayarlariAc(self):
        self.ctx.Ayarlar(self.ctx)
        if debug: self.ctx.logYaz(f'ayarlariAc: Ayarlar açıldı/kapandı.')

    def ayarlariOku(self):
        global online, debug
        os.makedirs(anaKlasor, exist_ok=True)
        if not os.path.isfile(logfile):
            with open(logfile, 'w') as dosya:
                dosya.write('Yeni Dosya')
                dosya.close()
        debug = self.ctx.ayarOku('Ayar', 'debug')
        if debug == 'Evet':
            debug = True  # konsola bilgi yaz
        else:
            debug = False
        self.ctx.ayarYaz('Ayar', 'debug', 'Evet' if debug else 'Hayir')
        online = self.ctx.ayarOku('Ayar', 'online')
        if online == 'Hayir':
            online = False  # sayfaları internetten mi alsın, kayıttan mı?
        else:
            online = True
        self.ctx.ayarYaz('Ayar', 'online', 'Evet' if online else 'Hayir')
        ayarDeger = self.ctx.ayarOku('Ayar', 'TimerDk')
        if ayarDeger is None: ayarDeger = '1' #1 dakikada bir kontrol
        self.ctx.TimerDk = int(ayarDeger)
        ayarDeger = self.ctx.ayarOku('DersProgram', 'GuncellemeDk')
        if ayarDeger is None: ayarDeger = '120' #ders programı online güncelleme
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
        self.ctx.Mesaj = self.ctx.ayarOku('Login','Mesaj') #gelen mesaj sayısı, en son

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
        with open(cerezF, 'wb') as dosya:
            pickle.dump(cerezler, dosya)
            dosya.close()

    def cerezOku(self):
        global cerezF
        try:
            with open(cerezF, 'rb') as dosya:
                cerezler = pickle.load(dosya)
                dosya.close()
        except:
            cerezler = None
        return cerezler

    def responseYaz(self, dosyaadi, icerik):
        with open(dosyaadi, 'w', encoding="utf8") as dosya:
            if debug: self.ctx.logYaz(f'responseYaz: {dosyaadi} yazıldı')
            dosya.write(icerik)
            dosya.close()

    def bugun(self):
        return datetime.now().strftime("%d.%m.%Y")

    def bugunmu(self, gun1):
        return gun1 == self.ctx.bugun()

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
        if ust < alt:
            gecengun=(datetime.strptime(tarih,'%d.%m.%Y') - datetime.strptime(bugun,'%d.%m.%Y')).days
            ust = ust + (86400 * gecengun)
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
            self.ctx.KulAdSifAl(self.ctx)
        else:
            kullanici['kullanici_adi'] = self.ayarOku('Kullanici', 'kullanici_adi')
            kullanici['sifre'] = base64.b64decode(bytearray(self.ayarOku('Kullanici', 'sifre'), 'utf-8')).decode(
                'utf-8')
        # if debug: QMessageBox.question(self.main_window, 'Ayar yap', 'Ayarlar Okundu', QMessageBox.Ok)
        if debug: self.ctx.TimedMessageBox('ayarLogin', 'Kullanıcı adı/şifre Okundu', QMessageBox.Ok, 3)
        return kullanici

    def loginKontrol(self):
        cerezler = self.cerezOku()
        try:
            if online:
                yanit = requests.get(adres + '/mesajlar', cookies=cerezler)
                sayfa = yanit.text
                self.responseYaz(anaKlasor + '\\oys-mesaj.html', sayfa)
                durum = yanit.status_code
            else:
                with open(anaKlasor + '\\oys-mesaj.html', 'r', encoding="utf8") as dosya:
                    durum = 'Offline <200>'
                    sayfa = dosya.read()
                    dosya.close()
            soup = BeautifulSoup(sayfa, features='html.parser')
            if soup.find('div', {'class': 'alert alert-danger'}):
                if debug: self.ctx.logYaz("loginKontrol: Kullanıcı/Şifre hatalı!!! ")
                self.ctx.loggedIn = False
                return None
            if soup.find('span', {'class': 'username username-hide-on-mobile'}):
                kullanici_adi = soup.find('span', {'class': 'username username-hide-on-mobile'}).text
                self.ayarYaz('Login', 'kullanici_adi', kullanici_adi)
                self.ctx.loggedIn = True
                if debug: self.ctx.logYaz(f'loginKontrol: kullanici_adi={kullanici_adi} status={durum}')
            else:
                if debug: self.ctx.logYaz('loginKontrol: kullanici_adi bulunamadı! Giriş yapın.')
                self.main_window.btn_Login.setVisible(True)
                self.ctx.loggedIn = False
                kullanici_adi = None
        except requests.exceptions.RequestException as e:
            if debug: self.ctx.logYaz(f'loginKontrol: HATA e={e}')
            self.ctx.loggedIn = False
            kullanici_adi = self.login()
        except requests.HTTPError as e:
            if debug: self.ctx.logYaz(f'loginKontrol: HATA e={e}')
            self.ctx.loggedIn = False
            kullanici_adi = self.login()
        return kullanici_adi

    def login(self):
        kullanici = self.ayarLogin()
        if online:
            # sayfa = urllib.request.urlopen(adres)
            sayfa = requests.get(adres).text
            self.responseYaz(anaKlasor + '\\oys-ana.html', sayfa)
        else:
            with open(anaKlasor + '\\oys-ana.html', 'r', encoding="utf8") as dosya:
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
        if online:
            response = requests.post(adres + '/login', data=kullanici)
            sayfa = response.text
            self.responseYaz(anaKlasor + '\\oys-login.html', sayfa)
            # if debug: print('login: sayfa=', sayfa)
            cerezler = response.cookies
        else:
            with open(anaKlasor + '\\oys-login.html', 'r', encoding="utf8") as dosya:
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


class AnaPencere(QMainWindow):
    def __init__(self, ctx):
        super(AnaPencere, self).__init__()
        self.ctx = ctx
        self.ctx.ayarlariOku()
        version = self.ctx.build_settings['version']
        self.title = 'OYS-Yesevi otomatik ders izleme v' + version
        self.setWindowTitle(self.title)
        self.resize(250, 150)
        kullanici_adi = self.ctx.ayarOku('Login', 'kullanici_adi')
        self.anaform = QWidget(self)
        self.anaVLayout = QVBoxLayout(self.anaform)
        self.anaLayout = QHBoxLayout(self.anaform)
        self.anaVLayout.addLayout(self.anaLayout)
        self.anaform.setLayout(self.anaLayout)
        self.setCentralWidget(self.anaform)
        self.lblOnOff = QLabel('(Online)' if online else '(Offline)', self.anaform)
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
        self.btn_Login.setVisible(False)
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
        self.ctx.online = online
        self.ctx.online = False
        b = scoGezgini(self.ctx)

    def setupMenu(self):
        menu = self.menuBar().addMenu("&Dosya")
        # ayar menüsü
        ayarlari_ac = QAction('&Ayarlar', self)
        ayarlari_ac.triggered.connect(self.ctx.ayarlariAc)
        menu.addAction(ayarlari_ac)
        #ders programı menüsü
        ders_programi_ac = QAction('&Ders Programı', self)
        ders_programi_ac.triggered.connect(self.dersProgramiAc)
        menu.addAction(ders_programi_ac)
        #sco gezgini menüsü
        scoGezginiAc=QAction('&SCO Gezgini', self)
        scoGezginiAc.triggered.connect(self.scogezginiac)
        menu.addAction(scoGezginiAc)
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

    def dersProgramDoldur(self):
        dersler = self.ders_program_kontrol()
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

    def initUI(self):
        self.setWindowTitle(self.title)
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(6)
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

    def getCommonInfo(self, oturum):
        cerezler = self.ctx.cerezOku()
        cerezler['BREEZESESSION'] = oturum
        sonuc = requests.get('http://sanal.yesevi.edu.tr/api/xml?action=common-info', cookies=cerezler)
        soup = BeautifulSoup(sonuc.text, 'lxml')
        name = soup.find('name').text
        login = soup.find('login').text
        user = soup.find('user')
        if user is not None:
            user_id = user['user-id']
        else:
            user_id = None
        return user_id, login, name

    def oturumGetir(self, cerezler):
        veri = {'page': 'get-badge-data', 'sg': ''}
        response = requests.post(adres + '/getMessagePage', data=veri, cookies=cerezler)
        sonuc = response.json()
        mesaj = eval(sonuc['Deger'])
        if debug: print(f"oturumGetir: Gelen Mesaj Sayısı={mesaj['GELEN']}, Giden Mesaj={mesaj['GIDEN']}")
        if mesaj['GELEN'] > 0:
            self.ctx.main_window.lblMesaj.setText(f"Mesaj: {mesaj['GELEN']}")
            self.ctx.TimedMessageBox("oturumGetir", f"Mesajınız Var ({mesaj['GELEN']})")
        else:
            self.ctx.main_window.lblMesaj.setText(f"Mesaj: {0}")
        self.ctx.ayarYaz('Login', 'Mesaj', str(mesaj['GELEN']))
        veri = {'page': 'GTACSI', 'sg': ''}
        response = requests.post(adres + '/getMessagePage', data=veri, cookies=cerezler)
        sonuc = response.json()
        oturum = sonuc['Deger']
        if debug: self.ctx.logYaz(f'oturumGetir: session={oturum}')
        self.ctx.ayarYaz('Login', 'oturum', oturum)
        return oturum

    def ders_programi_getir(self):
        global dersler
        dersler = []
        if online:
            if self.ctx.loginKontrol() is None:
                if debug: self.ctx.logYaz("dersProgramiGetir: Giriş Yapılmadı, iptal?")
                self.ctx.login()
            cerezler = self.ctx.cerezOku()
            response = requests.post(adres + '/ders_islemleri_ekran', cookies=cerezler)
            yanit = response.text
            self.ctx.responseYaz(anaKlasor + '\\oys-ders.html', yanit)
            oturum = self.oturumGetir(cerezler)
        else:
            with open(anaKlasor + '\\oys-ders.html', 'r', encoding="utf8") as dosya:
                yanit = dosya.read()
                dosya.close()
            oturum = self.ctx.ayarOku('Login', 'oturum')
        soup = BeautifulSoup(yanit, features='html.parser')
        if self.ctx.dpKaynak == 'Liste':
            bulunandersler = soup.find_all('div', {'class': 'card hover make-it-slow card-items'})
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
        aralik = self.ctx.dersDakika + (self.ctx.TimerDk if self.ctx.tekraracma else self.ctx.TekrarEnGec)
        aralikli= kalan + aralik - self.ctx.dersDakika
        if aralikli >= 0 and aralikli <= aralik:
            aralikta = True
        return kalan, aralikli, aralikta

    def gecerliSaatler(self, saat1):
        if datetime.strptime(saat1, '%H:%M') >= datetime.strptime(self.ctx.minSaat, '%H:%M') and datetime.strptime(
                saat1, '%H:%M') <= datetime.strptime(self.ctx.maxSaat, '%H:%M'):
            if debug: self.ctx.logYaz(
                f">>>>>gecerliSaatler: min={self.ctx.minSaat} max={self.ctx.maxSaat} Şimdi={saat1}<<<<<")
            return True
        else:
            if debug: self.ctx.logYaz(
                f"<<<<<gecerliSaatler: min={self.ctx.minSaat} max={self.ctx.maxSaat} Şimdi={saat1}>>>>>")
            return False

    def ders_program_kontrol(self):
        global ilkders, dersler
        bugunku = 999
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
            if debug: print(f"ders_program_kontrol: i={i} ilkders={ilkders:+1d} aralikta mi={'Evet' if acilsin else 'Hayır'} aralık={aralik:+4d} bugunku={bugunku:+4d}", dersler[i])
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
            #webbrowser.open('http://sanal.yesevi.edu.tr/login?session=' + oturum)
            webbrowser.open(dersurl)
            user_id, login, name = self.getCommonInfo(oturum)
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


if __name__ == '__main__':
    appctxt = AppContext()  # 4. Instantiate the subclass
    exit_code = appctxt.run()  # 5. Invoke run()
    sys.exit(exit_code)

'''TODO
'''
'''INFO
http://sanal.yesevi.edu.tr/api/xml?action=common-info   breezesession almanın tavsiye edilen yolu
'''
