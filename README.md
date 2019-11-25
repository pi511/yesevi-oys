# yesevi-oys
Yesevi oys sisteminde dersleri saati geldiğinde otomatik başlatma uygulaması

Ders saati geldiğinde, özellikle de o güne yeni ders eklenmişse, derse girmeyi unutabilirsiniz.
Bu program ders saatinde tarayıcı sayfasını otomatik açar.
Eve gittiğinizde bilgisayarınızı açın, programı çalıştırın. Otomatik izlemeyi başlat deyin. Bilgisayarın sesini açın.

Ders başladığınız hocanızın "iyi akşamlar arkadaşlar" sesiyle, dersin başladığını anlayıp, derse katılabilirsiniz.


**Ayarlar** açıklaması:<br>
- Kaç dakika önce     : ders sayfası, ders saatinden kaç dakika önce açılsın.
- Debug (log tut)     : bir dosyaya (ve/veya konsola) debug bilgileri yazılsın
- Online (siteden al) : uygulama online mı çalışsın, yoksa indirdiği responselar üzerinden offline mı
- En erken, En geç ders saati : bu saatler dışında ders programı güncellemesi yapma, ders açma
- Dersi bir kez aç    : otomatik açılan sayfada problem olması halinde dakikada bir sayfayı tekrar aç





NOT: selenium driver kullanmadığım için, çerezleri varsayılan tarayıcıya aktarmıyor şimdilik. O yüzden varsayılan tarayıcıda oys'de oturum açın, oturum kapanmasın diye arşivden bir ders izleyin. Böylece otomatik izleme sağlıklı çalışacaktır.

webbrowser yerine selenium uygulamayı düşünüyorum ama uygulamaya yeni modüller dahil etmek istemediğim için erteliyorum.
