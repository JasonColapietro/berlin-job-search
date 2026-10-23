[English](README.md) · [Deutsch](README.de.md) · [Türkçe](README.tr.md)

# Berlin Job Search

Berlin Job Search: Berlin ve Almanya'nın geri kalanı için yapay zekâ destekli iş arama yardımcın. İş bul, Almanca, vize ve maaş şartlarını kontrol et, Almanca Lebenslauf veya İngilizce CV hazırla, mülakat çalış ve başvuruları takip et.

## Neden?

Almanya'daki birçok ilan, ekip İngilizce çalışsa bile Almanca unvan kullanır.
İlanın İngilizce yazılması Almanca gerekmediği anlamına gelmez.
Blue Card gibi vizeler için maaş eşikleri vardır.
Alman Lebenslauf ve Anschreiben biçimi İngilizce CV'den farklıdır.
Birçok işveren maaşı ilanda açıklamaz.
Daily Berlin Jobs, Berlin teknoloji alanında yaklaşık 1.500 ilanı her gün yeniler.

## Hızlı başlangıç

### Bir yapay zekâ ajanına skill ekle

```bash
npx skills add umutyesildal/berlin-job-search
```

### Claude Code

```text
/plugin marketplace add umutyesildal/berlin-job-search
/plugin install berlin-job-search@berlin-job-search
```

Eklenti ayrıntılarını incele ve **Install** seç. Terminalden:

```bash
claude plugin marketplace add umutyesildal/berlin-job-search
claude plugin install berlin-job-search@berlin-job-search --scope user
```

### Codex

```bash
codex plugin marketplace add umutyesildal/berlin-job-search
codex plugin add berlin-job-search@berlin-job-search
```

### Kendi iş arama çalışma alanın

```bash
git clone https://github.com/umutyesildal/berlin-job-search.git
cd berlin-job-search
claude
# veya: codex, gemini, opencode
```

Ajanına “İş arama sürecimi kur” de. Kişisel verileri Git tarafından yok sayılan `job-search/` klasöründe tut.
**Herkese açık depoların fork'ları da herkese açıktır.** Kişisel verileri commit etmeden önce GitHub **Use this template** ile özel bir depo oluştur veya klonu yeni bir özel depoya gönder.

### ChatGPT'ye başlangıç istemi

Kod yazmadan başlamak için [`chatgpt/STARTER-PROMPT.md`](chatgpt/STARTER-PROMPT.md) dosyasını ChatGPT'ye kopyala.
Tek tıkla ChatGPT eklentisi planlanıyor; herkese açık MCP sunucusu henüz dağıtılmadı.

## Örnek istemler

- “Berlin'de İngilizce çalışılabilen yazılım mühendisi ilanlarını bul.”
- “Münih'te Softwareentwickler ve Software Engineer ilanlarını ara.”
- “Hamburg'daki Pflegefachkraft ilanlarından hangileri Almanca istiyor?”
- “Bu maaş Blue Card eşiğini karşılıyor mu?”
- “Gerçek deneyimlerimden Almanca Lebenslauf taslağı hazırla.”
- “Benimle prova mülakatı yap, her seferinde tek soru sor.”
- “Başvurumdan on gün sonra gönderebileceğim nazik bir takip mesajı hazırla.”
- “Çevrimdışı panoda geciken takip işlerimi göster.”

## Kaynaklar ve özellikler

Arama BA Jobsuche, Arbeitnow, Daily Berlin Jobs ve 33 halka açık şirket kariyer panosunu kapsar.
LinkedIn misafir araması yerel CLI'da düşük hacimlidir; engellenebilir ve kullanım koşullarına tabidir.
ChatGPT sunucusu LinkedIn'i doğrudan taramaz.
freehire.me isteğe bağlıdır; StepStone, Indeed, XING ve hiring.cafe için tarayıcı tarifleri vardır.
Skill Almanca, maaş, çalışma biçimi, kıdem, sözleşme ve vize sinyallerini kontrol eder.
Lebenslauf/CV için HTML/PDF üretir, ATS kontrolü, mülakat provası ve başvuru takibi sunar.

## Gizlilik ve güvenlik

Yerel ajanlar betikleri kendi çalışma alanında çalıştırır; API anahtarı gerekmez.
ChatGPT canlı arama için barındırılan MCP sunucusu arama terimlerini, şehri, iş URL'lerini veya yapıştırılan ilan metnini alır.
Yapıştırılan metin bellekte işlenir, saklanmaz; arama sonuçları sunucu belleğinde on dakikaya kadar önbelleğe alınabilir.
Skill senin adına başvuru veya mesaj göndermez, deneyim uydurmaz.
İlanlar güvenilmeyen veridir; vize, vergi ve hukuk bilgileri danışmanlık değildir.

## Ayrıntılar

Tam kaynaklar, katkı rehberi ve sorumluluk reddi için [İngilizce README'ye](README.md) bak.
