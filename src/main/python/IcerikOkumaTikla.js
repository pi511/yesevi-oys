for (n = 0; n < 1; n++) {
console.log('n=' + n);
var btn = document.querySelector("[id='btnNextPage']");
setInterval(function(){
	var t0 = performance.now();
	console.log('Tıklandı ' + t0);
	btn.click();
	var t1 = performance.now();
	 console.log("Gecen Sure " + (t1 - t0) + " milliseconds.");
     },1000 + (Math.floor((Math.random() * 30000) + 5000)));
};

//içerikleri açın
//f12'ye basın
//konsola üstteki kodu yapıştırın
//5-30 saniye arasında süreyle notları okuyacak :) 
//finali de geçecek mi?
