from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QCoreApplication
from bs4 import BeautifulSoup
import os
import sys
import base64
import zipfile
import io, subprocess
from datetime import datetime
import speech_recognition as sr
from pydub import AudioSegment
import time
import wave

ARSIVKLASOR = '\\arsiv'

class dersArsiv(QDialog):
    def __init__(self, ctx):
        global debug
        super(dersArsiv, self).__init__()
        self.ctx = ctx
        uic.loadUi(self.ctx.get_resource('dersArsiv.ui'), self)
        debug = self.ctx.debug
        os.makedirs(self.ctx.anaKlasor + ARSIVKLASOR, exist_ok=True)
        self.cmbDersler.currentIndexChanged.connect(self.dersSecildi)
        self.buttonBox.accepted.connect(self.arsivIsle)
        # self.buttonBox.rejected.connect(self.cancel)
        durum = self.arsivListeGetir()
        if durum:
            self.cmbDersDoldur()
            self.exec_()
        else:
            self.ctx.TimedMessageBox('dersArsiv',f"Ders Arşivleri okunamadı!",QMessageBox.Ok, 3)

    def arsivListeGetir(self):
        dersler = []
        durum = True
        mydosya=self.ctx.anaKlasor + '\\oys-ders.html'
        if os.path.isfile(mydosya):
            dosyatarih = os.path.getmtime(mydosya)
            fark = self.ctx.tarihfarki(self.ctx.bugun(), self.ctx.date2gun(datetime.fromtimestamp(dosyatarih)) )
        else:
            fark = 0
        if not os.path.isfile(mydosya) or fark > 1:
            self.ctx.onlineOl()
            cerezler = self.ctx.cerezOku()
            yanit = self.ctx.getSession().post(self.ctx.adres + '/ders_islemleri_ekran', cookies=cerezler)
            yanit.encoding = 'UTF-8'
            sayfa = yanit.text
            self.ctx.responseYaz(mydosya, sayfa)
        else:
            sayfa = self.ctx.responseOku(mydosya)
        try:
            soup = BeautifulSoup(sayfa, features='html.parser')
            div=soup.find('div',{'class':'col-md-12 tab-pane active', 'id':'contentHaftalikDers'})
            bulunandersler = div.find_all('div', {'class': 'card hover make-it-slow card-items'})
            i = 0
            for bulunanders in bulunandersler:
                eleman = bulunanders.find('button', {'class': 'btn btn-outline-red'})
                # print(eleman)
                if eleman:
                    derskodu=eleman.attrs['derskodu']
                    dersAdi=eleman.attrs['dersadi']
                    dersSube=eleman.attrs['data-sube-adi']
                    durum, liste = self.arsivListeDers(derskodu, dersSube, fark)
                else:
                    if debug: print(f"arsivListeGetir: eleman={eleman} bulunanders={bulunanders} bulunandersler=", bulunandersler)
                    break
                # if not durum: break
                dersler.append({'Ders': dersAdi})
                dersler[i]['Arsiv'] = liste
                dersler[i]['Sube'] = dersSube
                dersler[i]['Kod'] = derskodu
                if debug: print(f"arsivListeGetir: {i} {dersler[i]}")
                durum = True
                i += 1
        except e:
            if debug: print(f"arsivListeGetir: Hata var",  sys.exc_info()[0] )
            durum = False
        self.dersler=dersler
        return durum


    def arsivListeDers(self, derskodu,sube, fark):
        arsiv = []
        durum = False
        mydosya = self.ctx.anaKlasor + ARSIVKLASOR + f"\\{sube}.html"
        veri = {'METHOD': 'GOA', 'ID':derskodu, 'sg':''}
        if not os.path.isfile(mydosya) or fark > 1 or self.ctx.online:
            self.ctx.onlineOl()
            cerezler=self.ctx.cerezOku()
            yanit = self.ctx.getSession().post(self.ctx.adres + '/ders_islemleri_ekran', data=veri, cookies=cerezler)
            yanit.encoding = 'UTF-8'
            if debug: print(f"arsivListeDers: fark={fark} mydosya={mydosya} veri={veri} yanit={yanit}")
            sonuc = yanit.json()
            basarili = sonuc['Basarili']
            if basarili: sonuc = base64.b64decode(bytearray(sonuc['Deger'],'utf-8')).decode('utf-8')
        else:
            sonuc = self.ctx.responseOku(mydosya)
            basarili = True
        if basarili:
            # if debug: print("arsivListeDers: sonuc=",sonuc)
            # print("ba=",bytearray(sonuc['Deger'],'utf-8'))
            self.ctx.responseYaz(mydosya, sonuc)
            soup = BeautifulSoup(sonuc, features='html.parser')
            buttonlar = soup.find_all('tr',{'style':'height:25px;'}) #"openMeeting(f'http://{self.ctx.SanalSrv}/p3v02p30wpso/');"
            for satir in buttonlar:
                eleman = satir.find('span',{'class':'hidden-xs'})
                if eleman:
                    tarih = eleman.text
                eleman = satir.find('button',{'class':'btn btn-xs green'})
                if eleman:
                    baglanti = eleman.attrs['onclick'].split("'")[1]
                    # print(f"baglanti={baglanti}")
                    durum = True
                    if debug: print(f"arsivListeDers: tarih={tarih} eleman={eleman}")
                    arsiv.append({'link':baglanti,'tarih':tarih})
                else:
                    if debug: print(f"arsivListeDers: icerik <button> düzgün gelmedi...{tarih}de arşiv yok mu?")
                    durum = False
        else:
            if debug: print(f"arsivListeDers: yanit.json düzgün gelmedi...")
            durum = False
        if debug: print(f"arsivListeDers: arsiv={arsiv}")
        return durum, arsiv

    def cmbDersDoldur(self):
        for ders in self.dersler:
            self.cmbDersler.addItem(ders['Ders'])
        self.cmbHaftaDoldur(0)

    def cmbHaftaDoldur(self,dersno):
        for arsiv in self.dersler[dersno]['Arsiv']:
            self.cmbHaftalar.addItem(f"{arsiv['tarih']} ({ arsiv['link']})")

    def dersSecildi(self, no):
        self.cmbHaftalar.clear()
        self.cmbHaftaDoldur(no)

    def arsivIsle(self):
        self.buttonBox.Cancel = True
        self.txtDurum.clear()
        dersno = self.cmbDersler.currentIndex()
        arsivno = self.cmbHaftalar.currentIndex()
        derskod = self.dersler[dersno]['Sube'][:8]
        dosyaadi = f"{derskod}-{arsivno:02}"
        flvdosya = 'cameraVoip_0_3.flv'
        klasor = self.ctx.anaKlasor + ARSIVKLASOR + f"\\{dosyaadi}"
        self.txtDurum.append("*** Çevrimiçi olunuyor...")
        QCoreApplication.processEvents()
        oturum = self.ctx.onlineOl()
        link=self.dersler[dersno]['Arsiv'][arsivno]['link']+f"output/filename.zip?download=zip&session={oturum}"
        self.txtDurum.append(f"*** Yükleniyor: {link}")
        QCoreApplication.processEvents()
        cerezler = self.ctx.cerezOku()
        yanit = self.ctx.getSession().get(link, cookies=cerezler)
        if yanit.status_code==200:
            z = zipfile.ZipFile(io.BytesIO(yanit.content))
            if debug: print(f"arsivIsle: ziptekiler=",z.namelist())
            # z.extractall(klasor)
            if self.ctx.ZipSilme:
                fileName = klasor + '\\' + dosyaadi + '.zip'
                with open(fileName, 'wb') as dosya:
                    for chunk in yanit.iter_content(chunk_size=512):
                        dosya.write(chunk)
            z.extract(flvdosya,klasor)
        else:
            self.txtDurum.append('*** Dosya yüklenemedi!')
            return
        inputF = klasor + '\\' + flvdosya
        dosyaadi = klasor + '\\' + dosyaadi
        outputW = dosyaadi + '.wav'
        self.txtDurum.append("*** Dosya wav'a çevriliyor...")
        QCoreApplication.processEvents()
        self.flv2wav(inputF, outputW)
        self.txtDurum.append('*** Wav dosya konuşmadan metne çevriliyor...')
        QCoreApplication.processEvents()
        self.recognizeWav(outputW, dosyaadi, self.txtDurum.append)
        self.txtDurum.append(f"*** {outputW} silindi.")
        self.txtDurum.append(f"*** {dosyaadi}.txt oluşturuldu...")
        subprocess.Popen(['notepad',dosyaadi+'.txt'])
        # os.system(f"notepad {dosyaadi}.txt")
        time.sleep(5)
        if self.ctx.FlvSilme:
            self.txtDurum.append(f"*** {inputF} silinmedi.")
        else:
            self.txtDurum.append(f"*** {inputF} silindi.")
            os.remove(inputF)
        os.remove(outputW)
        self.close()

    def flv2wav(self,dosya, output_file):
        ''' https://github.com/SV3A/connect-grabber/blob/master/connect-grabber.py '''
        if debug: print(f"flv2wav: input={dosya} output={output_file}")
        subprocess.call(['D:\\pi\\util\\ffmpeg\\ffmpeg.exe', '-i', dosya, '-f', 'wav', '-v', '0', '-y',output_file])

    def recognizeWav(self, wavfile, dosyaadi, logyazfunc):
        with wave.open(wavfile, 'r') as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            dur = int(duration)
        parca = int(dur / 60)
        for i in range(parca):
            t1 = i * 60 * 1000  # Works in milliseconds
            t2 = (i + 1) * 60 * 1000
            logyazfunc(f"recognizeWav: dakika={i}/{parca} (segment t1={t1}ms - t2={t2}ms)")
            QCoreApplication.processEvents()
            newAudio = AudioSegment.from_wav(dosyaadi + '.wav')     #wav segmentlemeye başla
            newAudio = newAudio[t1:t2] # t1-t2 segmentini al (1 dakikalık)
            newAudio.export(dosyaadi + str(i) + ".wav", format="wav") #segmenti dosyaya yaz
            r = sr.Recognizer() #ses tanımayı sıfırla
            harvard = sr.AudioFile(dosyaadi + str(i) + ".wav") #wav dosyayı girdi olarak al
            with harvard as source:
                audio = r.record(source)
            text = r.recognize_google(audio, show_all=True, language="tr-TR")
            if os.path.exists(dosyaadi + '.txt'):
                append_write = 'a'  # append if already exists
            else:
                append_write = 'w'  # make a new file if not
            with open(dosyaadi + '.txt', append_write) as txtDosya:
                txtDosya.write("\n[" + str(i) + ". dakika]")
                txtDosya.write(text["alternative"][0]['transcript'])
            os.remove(dosyaadi + str(i) + ".wav")

