from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton
from bs4 import BeautifulSoup
import os, sys
from datetime import datetime
import re
import json

class dersIcerik(QDialog):
    def __init__(self, ctx):
        global debug
        super(dersIcerik, self).__init__()
        self.ctx = ctx
        debug = self.ctx.debug
        self.title = 'Ders İçerikleri'
        self.initUI()
        if self.dersTabloAl():
            self.exec()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.tableWidget = QTableWidget()
        self.ctx.dersSayisi=6
        self.tableWidget.setRowCount(self.ctx.dersSayisi)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(['Ders Adı', 'Son Giriş Tarihi', 'Kalma Süresi', 'Gezinme Yüzdesi', 'Bağlantı'])
        self.tableWidget.setColumnWidth(0, 410)
        self.tableWidget.setColumnWidth(1, 110)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setColumnWidth(4, 400)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.buttonsLayout= QHBoxLayout()
        self.layout.addLayout(self.buttonsLayout)
        self.btn_Update = QPushButton('İçerik Durumlarını Güncelle', self)
        self.btn_Update.clicked.connect(self.btnUpdateClicked)
        self.buttonsLayout.addWidget(self.btn_Update)
        self.btn_Baslat = QPushButton('Seçilen Ders İçin Otomatik İçerik Okumayı Başlat', self)
        self.btn_Baslat.clicked.connect(self.btnBaslatClicked)
        self.buttonsLayout.addWidget(self.btn_Baslat)
        self.setLayout(self.layout)
        self.setGeometry(50, 50, 1150, 300)

    def btnUpdateClicked(self):
        self.dersTabloAl(True)

    def btnBaslatClicked(self):
        if self.tableWidget.selectedItems()!=[]:
            dersler=self.dersler
            secilen= self.tableWidget.selectedItems()[0].row()
            if debug: self.ctx.logYaz(f"BaslatClicked: Icerik okunacak ders={dersler[secilen]['Ders']}")
            self.dersIcerikOku(secilen)

    def dersTabloAl(self, guncelle=False):
        durum = False
        if not guncelle:
            durum, dersler = self.dbDersDurumOku()
        if not durum:
            durum, dersler = self.dersDurumGetir()
        if durum:
            self.dersDurumDoldur(dersler)
            self.dersler = dersler
            return True
        else:
            return False

    def dersDurumDoldur(self, dersler):
        if len(dersler) != self.ctx.dersSayisi:
            self.ctx.dersSayisi = len(dersler)
            self.tableWidget.setRowCount(self.ctx.dersSayisi)
        i = 0
        for ders in dersler:
            self.tableWidget.setItem(i, 0, QTableWidgetItem(ders['Ders']))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(ders['SonGiris']))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(ders['KalmaSure']))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(f"% {ders['Yuzde']:>5s}" ))
            self.tableWidget.setItem(i, 4, QTableWidgetItem(ders['Link']))
            i += 1
        # if ilkders > -1:
        #     if self.otomatik:
        #         self.tableWidget.item(ilkders, 2).setBackground(Qt.green)
        #     else:
        #         self.tableWidget.item(ilkders, 2).setBackground(Qt.white)
        if debug: self.ctx.logYaz(f'dersDurumDoldur: {i} ders dolduruldu')

    def dbDersDurumOku(self):
        dersler=[]
        if self.ctx.dbTableExists('derslerI'):
            cursor=self.ctx.dbCursor()
            cursor.execute('''SELECT ders, songiris, sure, yuzde, link FROM derslerI''')
            i=0
            for row in cursor:
                dersler.append({'Ders': row[0]})
                dersler[i]['SonGiris'] = row[1]
                dersler[i]['KalmaSure'] = row[2]
                dersler[i]['Yuzde'] = row[3]
                dersler[i]['Link'] = row[4]
                i+=1
            if debug: self.ctx.logYaz(f'dersDurumOku: {i} ders veritabanından okundu')
            return True, dersler
        else:
            return False, dersler

    def dbYazDersler(self, dersler):
        #veritabanına yaz
        cursor=self.ctx.dbCursor()
        if self.ctx.dbTableExists('derslerI'):
            cursor.execute('''DROP TABLE derslerI''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS
                        derslerI(ders TEXT, songiris TEXT, sure TEXT, yuzde TEXT, link TEXT)''')
        self.ctx.db.commit()
        for ders in dersler:
            cursor.execute(f'''INSERT INTO derslerI(ders, songiris, sure, yuzde, link)
                            VALUES('{ders['Ders']}','{ders['SonGiris']}','{ders['KalmaSure']}','{ders['Yuzde']}','{ders['Link']}')''')
        self.ctx.db.commit()


    def dersDurumGetir(self):
        dersler = []
        durum = True
        mydosya=self.ctx.anaKlasor + '\\oys-ders.html'
        if not os.path.isfile(mydosya):
            if self.ctx.loginKontrol() is None:
                if debug: self.ctx.logYaz("dersDurumGetir: Giriş Yapılmadı, iptal?")
                self.ctx.login()
            cerezler = self.ctx.cerezOku()
            response = self.ctx.getSession().post(self.ctx.adres + '/ders_islemleri_ekran', cookies=cerezler)
            yanit = response.text
            self.ctx.responseYaz(mydosya, yanit)
        else:
            with open(mydosya, 'r', encoding="utf-8") as dosya:
                yanit = dosya.read()
                dosya.close()
        try:
            soup = BeautifulSoup(yanit, features='html.parser')
            div=soup.find('div',{'class':'col-md-12 tab-pane active', 'id':'contentHaftalikDers'})
            bulunandersler = div.find_all('div', {'class': 'card hover make-it-slow card-items'})
            i = 0
            for bulunanders in bulunandersler:
                eleman = bulunanders.find('button', {'class': 'btn btn-outline-linkedin lesson-state'})
                if eleman:
                    icerikno=eleman.attrs['onclick'].split('"')[1]
                    durum, ders = self.dersIcerikDrm(icerikno)
                else:
                    print(eleman, "bulunanders=", bulunanders,"bulunandersler=", bulunandersler)
                    break
                if not durum: break
                dersler.append({'Ders': ders[0].strip()})
                dersler[i]['SonGiris'] = ders[1].strip()
                dersler[i]['KalmaSure'] = ders[2].strip()
                dersler[i]['Yuzde'] = ders[3].strip()
                eleman = bulunanders.find('button', {'class': 'btn btn-outline-purple'})
                # print(eleman)
                icerikno=eleman.attrs['derskodu']
                durum, dersler[i]['Link'] = self.dersIcerikLink(icerikno)
                if debug: print(f"dersDurumGetir:{i} {dersler[i]}")
                i += 1
            self.dbYazDersler(dersler)
        except e:
            print("Hata var",  sys.exc_info()[0] )
            durum = False
        return durum, dersler

    def dersIcerikDrm(self, icerikno):
        ders = []
        veri = {'METHOD': 'GODRM', 'Mode': 'List', 'SID':icerikno, 'sg':''}
        self.ctx.onlineOl()
        cerezler=self.ctx.cerezOku()
        yanit = self.ctx.getSession().post(self.ctx.adres + '/ders_islemleri_ekran', data=veri, cookies=cerezler)
        sonuc = yanit.json()
        basarili = sonuc['Basarili']
        if basarili:
            # print('sonuc=', sonuc)
            soup = BeautifulSoup(sonuc['Deger'], features='html.parser')
            derstr = soup.find('tbody',{'id':'IcerikteKalmaSuresi'}).find('tr')
            if derstr:
                derstr = derstr.text
                # print(f"derstr={derstr}")
                # td = derstr.find('<td>')
                # while td>-1:
                #     derstr=derstr[td+4]
                #     print(f"derstr={derstr} td={td}")
                #     td = derstr.find('<td>')
                #     ders.append(derstr[td])
                ders=derstr.split('         ')
                durum = True
            else:
                ders[0]='derstr düzgün gelmedi...'
                durum = False
        else:
            ders[0]= 'yanit.json düzgün gelmedi...'
            durum = False
        if debug: print(f"dersIcerikDrm: {durum} <tr>'den split edilen ders={ders}")
        return durum, ders

    def dersIcerikLink(self, icerikno):
        ders = []
        veri = {'METHOD': 'GODIL', 'ID':icerikno, 'sg':''}
        self.ctx.onlineOl()
        cerezler=self.ctx.cerezOku()
        yanit = self.ctx.getSession().post(self.ctx.adres + '/ders_islemleri_ekran', data=veri, cookies=cerezler)
        sonuc = yanit.json()
        basarili = sonuc['Basarili']
        if basarili:
            # print('sonuc=', sonuc)
            soup = BeautifulSoup(sonuc['Deger'], features='html.parser')
            eleman = soup.find('a',{'class':'btn btn-xs btn-outline-purple'})
            if eleman:
                baglanti=eleman.attrs['onclick'].split("'")[1]
                # print(f"baglanti={baglanti}")
                durum = True
            else:
                ders[0]='icerik <a> düzgün gelmedi...'
                durum = False
        else:
            ders[0]= 'yanit.json düzgün gelmedi...'
            durum = False
        if debug: print(f"dersIcerikLink: <a onClick=jQuery.openCourseContents({baglanti})")
        return durum, baglanti

    def dersIcerikOku(self, secilen):
        if debug: print(f"dersIcerikOku: secilen ders[{secilen}]={self.dersler[secilen]}")
        mydosya=self.ctx.anaKlasor + f"\\oys-icerik-{self.dersler[secilen]['Ders'][:8]}.html"
        self.ctx.onlineOl()
        cerezler = self.ctx.cerezOku()
        if not os.path.isfile(mydosya):
            sonuc = self.ctx.getSession().get(self.dersler[secilen]['Link'], cookies=cerezler)
            yanit = sonuc.text
            self.ctx.responseYaz(mydosya, yanit)
        else:
            with open(mydosya, 'r', encoding="utf-8") as dosya:
                yanit = dosya.read()
                dosya.close()
        soup = BeautifulSoup(yanit, features='html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            # if debug: print(f"dersIcerikOku: script={script}")
            script=script.text
            if 'var arrayData' in script:
                script =  re.findall('=(.*?;)', script)
                jArray = script[0][:-1]
                print ("jArray=",jArray)
                arrayData = json.loads(jArray)
                jArray = script[1][1:-2]
                print("jArray=", jArray)
                ogrStatus = json.loads(jArray)
        if debug: print(f"dersIcerikOku: len={len(arrayData)} arrayData=", arrayData)
        if debug: print(f"dersIcerikOku: len={len(ogrStatus)} ogrStatus=", ogrStatus)
        veri = {'GMOD': 'Start'}
        yanit = self.ctx.getSession().post(self.dersler[secilen]['Link'], data=veri, cookies=cerezler)
        # if debug: print(yanit.text)
        sonuc = yanit.json()
        basarili = sonuc['Basarili']
        if basarili:
            print("ok")
            ks, ss, dizin = self.dizinOlustur(arrayData)
            ss += ks
            if debug: print(f"dersIcerikOku: klasör={ks} sayfa={ss}")
            i = 0
            for o in ogrStatus:
                if o['PDIH_ICERIK_SURE'] < 10:
                    print(f"{self.ctx.adres}/index.php?Reque=dersIcerikView&dersManifest={dizin[i]['ss']}&manifestKey={dizin[i]['kk']}&DP={dizin[i]['dp']}&ss={ss}")
                i += 1

            # print("dizin=",dizin)

    def dizinOlustur(self, arrayData):
        dizin = []
        ss = 0
        ks = 0
        i = -1
        for a in arrayData:
            i += 1
            elem = a[0]
            if debug: print(f"dizinOlustur: i={i} elem={elem['text']} a.value={elem['value']}")
            if elem['value'] is None:
                dizin.append({'tip': 'sayfa'})
                dizin[i]['dp'] = elem['text']
                dizin[i]['ss'] = elem['link']
                dizin[i]['kk'] = elem['key']
                dizin[i]['dp'] = elem['ders']
                ss += 1
            else:
                dizin.append({'tip': 'klasor'})
                dizin[i]['dp'] = elem['text']
                dizin[i]['ss'] = elem['link']
                dizin[i]['kk'] = elem['key']
                dizin[i]['dp'] = elem['ders']
                ks += 1
                k, s, alt = self.dizinOlustur(elem['value'])
                ks += k
                ss += s
                dizin += alt
                i += len(alt)
        if debug: print(f"dizinOlustur: klasör={ks} sayfa={ss} i={i}")
        return ks, ss, dizin


if __name__ == '__main__':
    print('main.py çalıştır')
