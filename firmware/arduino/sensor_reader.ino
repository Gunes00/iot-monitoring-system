/**
 * IoT Monitoring System - Sensor Reader
 * 
 * Bu kod DHT22, BMP280 ve MQ-135 sensörlerinden veri okuyup 
 * MQTT üzerinden bir Raspberry Pi'ye iletir.
 * 
 * @author Gunes00
 * @license MIT
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <DHT.h>
#include <Adafruit_BMP280.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Pin tanımları
#define DHTPIN 2
#define DHTTYPE DHT22
#define MQ135_PIN A0
#define MOTION_PIN 4
#define LED_PIN 5

// Ağ ayarları
const char* WIFI_SSID = "WIFI_SSID";
const char* WIFI_PASSWORD = "WIFI_PASSWORD";
const char* MQTT_SERVER = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "sensors/data";
const char* MQTT_CLIENT_ID = "arduino_sensor_node";

// Sensör nesneleri
DHT dht(DHTPIN, DHTTYPE);
Adafruit_BMP280 bmp;

// MQTT ve WiFi nesneleri
WiFiClient espClient;
PubSubClient client(espClient);

// Zamanlama değişkenleri
unsigned long lastSensorReadTime = 0;
const long sensorReadInterval = 10000; // 10 saniye

void setup() {
  Serial.begin(115200);
  pinMode(MOTION_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Sensörleri başlat
  dht.begin();
  
  if (!bmp.begin()) {
    Serial.println(F("BMP280 sensörü bulunamadı!"));
  }
  
  // WiFi'yi yapılandır
  setupWifi();
  
  // MQTT'yi yapılandır
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
  
  Serial.println("Sistem başlatıldı!");
}

void loop() {
  // MQTT bağlantısını kontrol et
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Belirli aralıklarla sensörleri oku
  unsigned long currentMillis = millis();
  if (currentMillis - lastSensorReadTime >= sensorReadInterval) {
    lastSensorReadTime = currentMillis;
    readAndPublishSensorData();
  }
  
  // Hareket sensörünü kontrol et
  checkMotion();
}

void setupWifi() {
  delay(10);
  Serial.println();
  Serial.print("WiFi ağına bağlanılıyor: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi bağlandı");
  Serial.print("IP adresi: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  // MQTT üzerinden gelen komutları işleyin
  char message[length + 1];
  for (int i = 0; i < length; i++) {
    message[i] = (char)payload[i];
  }
  message[length] = '\0';
  
  Serial.print("Mesaj alındı [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);
  
  // LED kontrolü
  if (String(topic) == "sensors/control" && String(message) == "LED_ON") {
    digitalWrite(LED_PIN, HIGH);
  } else if (String(topic) == "sensors/control" && String(message) == "LED_OFF") {
    digitalWrite(LED_PIN, LOW);
  }
}

void reconnect() {
  // MQTT sunucusuna bağlan
  while (!client.connected()) {
    Serial.print("MQTT sunucusuna bağlanılıyor...");
    if (client.connect(MQTT_CLIENT_ID)) {
      Serial.println("bağlandı");
      client.subscribe("sensors/control");
    } else {
      Serial.print("bağlantı başarısız, rc=");
      Serial.print(client.state());
      Serial.println(" 5 saniye içinde tekrar denenecek");
      delay(5000);
    }
  }
}

void readAndPublishSensorData() {
  // DHT22'den sıcaklık ve nem oku
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  // BMP280'den basınç ve yükseklik oku
  float pressure = bmp.readPressure() / 100.0F; // hPa cinsinden
  float altitude = bmp.readAltitude(1013.25); // Deniz seviyesi referans basıncı
  
  // MQ-135'den hava kalitesi oku
  int airQuality = analogRead(MQ135_PIN);
  
  // Değerleri kontrol et
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println(F("DHT22'den okuma başarısız!"));
    return;
  }
  
  // JSON formatında veriyi hazırla
  StaticJsonDocument<256> doc;
  doc["node_id"] = MQTT_CLIENT_ID;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["pressure"] = pressure;
  doc["altitude"] = altitude;
  doc["air_quality"] = airQuality;
  doc["timestamp"] = millis();
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  // MQTT üzerinden veriyi gönder
  Serial.print("Veri gönderiliyor: ");
  Serial.println(buffer);
  client.publish(MQTT_TOPIC, buffer);
}

void checkMotion() {
  int motionDetected = digitalRead(MOTION_PIN);
  
  if (motionDetected == HIGH) {
    StaticJsonDocument<128> doc;
    doc["node_id"] = MQTT_CLIENT_ID;
    doc["event"] = "motion_detected";
    doc["timestamp"] = millis();
    
    char buffer[128];
    serializeJson(doc, buffer);
    
    // Hareket algılandı mesajını gönder
    client.publish("sensors/events", buffer);
    
    // LED'i yakıp söndür
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
  }
}