# yesevi-oys
Yesevi oys sisteminde dersleri saati geldiğinde otomatik başlatma uygulaması

Ders saati geldiğinde, özellikle de o güne yeni ders eklenmişse, derse girmeyi unutabilirsiniz.
Bu program ders saatinde tarayıcı sayfasını otomatik açar.
Eve gittiğinizde bilgisayarınızı açın, programı çalıştırın. Otomatik izlemeyi başlat deyin. Bilgisayarın sesini açın.

Ders başladığınız hocanızın "iyi akşamlar arkadaşlar" sesiyle, dersin başladığını anlayıp, derse katılabilirsiniz.
===============================================================================<br>
ScoGezgini menüsünden:
  - Derslere ait sunumları indirebilirsiniz.
  - Takvimden ders günü seçtiğinizde alt kutuya o günkü dersler listelenir.
  - Alt kutudan dersi seçtiğinizde o derse ait indirilebilecek dosyalar sağ kutuya listelenir.
  - Sağ kutuda dosya seçip Save butonuna bastığınızda dosya sistemde indirilebilir halde mevcut ise indirilir.
  - Dosya aynı ad ile ulaşılamıyorsa, derse ait içerik (swf slide oynatıcı ile beraber) zip olarak indirilir.
  - Not: dosyalar bazen sco ile belirtilen yolda değil, diğer yolda olabiliyor. Sistemin admin tarafında işleyişini bilmediğimden tahminimce
  - pdf'den ppt'ye, pptx'e vs çevrimler sonunda bir kaç dosya sco'su oluşuyor.
  - Bunlardan birinin url'sinde diğerinin dosya adını indirebiliyorsunuz. Bu mantığı programla kurmak istemedim.
  - Bunun yerine dosya adlarının yanın sco-depth'lerini yazdım. Derinlik 2 olan daha kuvvetle muhtemel inecektir.
  - İlle de o dosyayı manuel indirmek isterseniz buradaki açıklamaları takip edin:
  - https://tarikozcan.wordpress.com/2017/07/14/turtepte-sanal-derste-gosterilen-sunulari-indirmek/

**Ayarlar** açıklaması:<br>
- Kaç dakika önce     : ders sayfası, ders saatinden kaç dakika önce açılsın. def=3
- Debug (log tut)     : bir dosyaya (ve/veya konsola) debug bilgileri yazılsın def=hayır
- Online (siteden al) : uygulama online mı çalışsın, yoksa indirdiği responselar üzerinden offline mı def:evet
- En erken, En geç ders saati : bu saatler dışında ders programı güncellemesi yapma, ders açma def:17.30-23.30
- Timer kontrol dakika: otomatik işlemler kaç dakikada bir çalışsın (program kontrol) def=1
- Ders program güncelleme     : ders programını siteden ne periyodda güncellesin def=120
- Kaynak              : Liste (ders listesinden oku) Program (ders programından oku)
- Dersi bir kez aç    : otomatik açılan sayfada problem olması halinde dakikada bir sayfayı tekrar aç def=açma
- En geç kaç dk.      : dersi birden fazla açacaksa, ders saatinden en geç kaç dk. sonra tekrar açsın (timer kontrol dakika'da belirtilen dk.da bir açılacak) def=10

===============================================================================<br>
Python içinden kullanabilmek için ilgili modülleri kurmalısınız. (pip install ...)
exe'ye çevirmek için fbs modülünü indirip, aynı klasör yapısını oluşturun. Scriptlerden sanal ortamı activate.bat ile aktifleştirin.
"fbs freeze" ile exe'ye çevirebilirsiniz.

Veya <a href=https://1drv.ms/u/s!AnY5SpLroMRqlZQDVdwOXJoE7Oy0DQ> kurulum paketi</a> ile windowsa kurup kullanabilirsiniz. (windows 10 ve 2012'da denendi)


NOT: selenium driver kullanmadığım için, çerezleri varsayılan tarayıcıya aktarmıyor şimdilik. O yüzden varsayılan tarayıcıda oys'de oturum açın, oturum kapanmasın diye arşivden bir ders izleyin. Böylece otomatik izleme sağlıklı çalışacaktır.

webbrowser yerine selenium uygulamayı düşünüyorum ama uygulamaya yeni modüller dahil etmek istemediğim için erteliyorum.
