# NexPanel

Termux üzerinde çalıştırmak için hazırlanmış güçlü bir sorgu paneli.

## Gereksinimler

- Python 3.10+
- Termux veya herhangi bir Linux tabanlı ortam

## Kurulum

1. Proje klasörünü indirin veya oluşturun:

```bash
mkdir -p ~/NexPanel
cd ~/NexPanel
```

2. Gerekli dosyaları buraya kopyalayın.

3. Python paketleri kurmaya gerek yok; standart kütüphane yeterlidir.

4. Uygulamayı başlatın:

```bash
python3 app.py
```

5. Tarayıcıda açın:

```text
http://127.0.0.1:8000
```

## Termux'ta çalışan örnek akış

```bash
pkg update && pkg upgrade
pkg install python
cd ~/NexPanel
python3 app.py
```

## Durdurma

- Terminalde Ctrl + C basın.

## GitHub'dan kurulum (Tam adım adım)

Eğer projeyi GitHub'dan indirdiyseniz, Termux'ta şu şekilde kurabilirsiniz:

```bash
pkg update && pkg upgrade
pkg install git python
cd ~
git clone https://github.com/ginbesse/NexPanel.git
cd NexPanel
python3 app.py
```

### Eğer repo zaten yüklü ise

```bash
cd ~/NexPanel
git pull
python3 app.py
```

### Tarayıcıda açma

```text
http://127.0.0.1:8000
```

### Durdurma

- Terminalde Ctrl + C basın.

## Özellikler

- MEB öğrenci notları sorgusu
- MEB e-okul bağlantısı
- Harita servisi çağrısı
- Belsis sorgu servisleri
- Türkiye.gov.tr Adli Sicil Kaydı inceleme
