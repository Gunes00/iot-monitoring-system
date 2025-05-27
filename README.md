# IoT Monitoring System 🌐🔌

Akıllı sensör izleme ve kontrol sistemi. C/C++ ve Python ile geliştirilmiştir.

![C++](https://img.shields.io/badge/-C++-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![Python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/-Raspberry%20Pi-C51A4A?style=for-the-badge&logo=raspberry-pi&logoColor=white)
![Arduino](https://img.shields.io/badge/-Arduino-00979D?style=for-the-badge&logo=arduino&logoColor=white)

## 📋 Proje Özeti

Bu proje, çeşitli sensörlerden veri toplamak, bu verileri işlemek ve bulut tabanlı bir dashboard üzerinden görselleştirmek için tasarlanmış tam kapsamlı bir IoT sistemidir. Donanım kontrolleri C/C++ ile, veri işleme ve web arayüzü Python ile geliştirilmiştir.

## ✨ Özellikler

- 🌡️ Sıcaklık, nem, basınç, hareket vb. sensörlerden veri toplama
- 📊 Gerçek zamanlı veri izleme ve kayıt
- 🚨 Belirli koşullarda uyarı ve bildirim sistemi
- 📱 Mobil uyumlu web arayüzü
- 🔐 Güvenli veri iletişimi (MQTT, SSL/TLS)
- 🔄 OTA (Over-The-Air) güncellemeleri
- 🧠 Basit makine öğrenimi ile anormallik tespiti

## 🔧 Donanım Gereksinimleri

- Raspberry Pi (3 veya üzeri)
- Arduino (isteğe bağlı, ek sensörler için)
- Sensörler:
  - DHT22 (Sıcaklık/Nem)
  - BMP280 (Basınç/Yükseklik)
  - PIR (Hareket)
  - MQ-135 (Hava Kalitesi)
- Röle modülü (cihaz kontrolü için)

## 📁 Repo Yapısı

```
/
├── firmware/           # C/C++ kaynak kodları
│   ├── arduino/        # Arduino için sensör okuma
│   └── rpi/            # Raspberry Pi için ana kontrol
├── server/             # Python backend kodları
│   ├── api/            # REST API
│   ├── db/             # Veritabanı işlemleri
│   └── ml/             # Makine öğrenimi modülleri
├── web/                # Web arayüzü
├── docs/               # Dokümanlar ve şemalar
└── tools/              # Yararlı araçlar ve scriptler
```

## 🚀 Kurulum

### Firmware (Raspberry Pi)

```bash
cd firmware/rpi
make
sudo ./install.sh
```

### Server

```bash
cd server
pip install -r requirements.txt
python app.py
```

## 📝 Yapılacaklar

- [ ] Daha fazla sensör desteği
- [ ] MQTT optimizasyonu
- [ ] Gelişmiş anomali tespiti
- [ ] Mobil uygulama geliştirme
- [ ] Enerji verimliliği iyileştirmeleri

## 📄 Lisans

MIT