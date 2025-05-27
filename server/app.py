#!/usr/bin/env python3
"""
IoT Monitoring System - Server Application

Bu uygulama sensörlerden gelen verileri işler, veritabanında saklar
ve bir web API aracılığıyla erişilebilir hale getirir.

@author Gunes00
@license MIT
"""

import os
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import paho.mqtt.client as mqtt
import sqlite3
import pandas as pd
from flask_cors import CORS

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask uygulaması
app = Flask(__name__)
CORS(app)  # Cross-Origin isteklerine izin ver

# Veritabanı yapılandırması
DB_FILE = "sensor_data.db"

# MQTT yapılandırması
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_DATA = "sensors/data"
MQTT_TOPIC_EVENTS = "sensors/events"
MQTT_TOPIC_CONTROL = "sensors/control"

def init_db():
    """Veritabanını oluştur ve tabloları hazırla"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Sensör verileri tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT NOT NULL,
        temperature REAL,
        humidity REAL,
        pressure REAL,
        altitude REAL,
        air_quality INTEGER,
        timestamp INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Olay kayıtları tablosu
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        timestamp INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Veritabanı başarıyla hazırlandı")

def on_connect(client, userdata, flags, rc):
    """MQTT bağlantısı kurulduğunda çağrılır"""
    logger.info(f"MQTT Broker'a bağlandı, sonuç kodu: {rc}")
    client.subscribe([(MQTT_TOPIC_DATA, 0), (MQTT_TOPIC_EVENTS, 0)])

def on_message(client, userdata, msg):
    """MQTT üzerinden mesaj alındığında çağrılır"""
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"Mesaj alındı: {msg.topic} - {payload}")
        
        if msg.topic == MQTT_TOPIC_DATA:
            save_sensor_data(payload)
        elif msg.topic == MQTT_TOPIC_EVENTS:
            save_event(payload)
    except Exception as e:
        logger.error(f"Mesaj işlenirken hata: {e}")

def save_sensor_data(data):
    """Sensör verilerini veritabanına kaydet"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        '''INSERT INTO sensor_data 
           (node_id, temperature, humidity, pressure, altitude, air_quality, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (
            data.get('node_id'),
            data.get('temperature'),
            data.get('humidity'),
            data.get('pressure'),
            data.get('altitude'),
            data.get('air_quality'),
            data.get('timestamp')
        )
    )
    
    conn.commit()
    conn.close()
    logger.info(f"Sensör verisi kaydedildi: {data.get('node_id')}")

def save_event(data):
    """Olay kaydını veritabanına kaydet"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        '''INSERT INTO events 
           (node_id, event_type, timestamp)
           VALUES (?, ?, ?)''',
        (
            data.get('node_id'),
            data.get('event'),
            data.get('timestamp')
        )
    )
    
    conn.commit()
    conn.close()
    logger.info(f"Olay kaydedildi: {data.get('node_id')} - {data.get('event')}")

def get_recent_data(hours=24):
    """Son verileri veritabanından getir"""
    conn = sqlite3.connect(DB_FILE)
    query = f"""
    SELECT * FROM sensor_data 
    WHERE created_at >= datetime('now', '-{hours} hours')
    ORDER BY created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_events(hours=24):
    """Son olayları veritabanından getir"""
    conn = sqlite3.connect(DB_FILE)
    query = f"""
    SELECT * FROM events 
    WHERE created_at >= datetime('now', '-{hours} hours')
    ORDER BY created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Flask rotaları
@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def api_data():
    """Sensör verilerini döndür"""
    hours = request.args.get('hours', default=24, type=int)
    node_id = request.args.get('node_id', default=None, type=str)
    
    df = get_recent_data(hours)
    
    if node_id:
        df = df[df['node_id'] == node_id]
    
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/events', methods=['GET'])
def api_events():
    """Olay kayıtlarını döndür"""
    hours = request.args.get('hours', default=24, type=int)
    node_id = request.args.get('node_id', default=None, type=str)
    
    df = get_events(hours)
    
    if node_id:
        df = df[df['node_id'] == node_id]
    
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """İstatistikleri döndür"""
    df = get_recent_data()
    
    if df.empty:
        return jsonify({"error": "Veri bulunamadı"})
    
    stats = {
        "node_count": df['node_id'].nunique(),
        "reading_count": len(df),
        "avg_temperature": round(df['temperature'].mean(), 2),
        "avg_humidity": round(df['humidity'].mean(), 2),
        "last_updated": df['created_at'].max()
    }
    
    return jsonify(stats)

@app.route('/api/control', methods=['POST'])
def api_control():
    """Cihazlara komut gönder"""
    data = request.json
    node_id = data.get('node_id')
    command = data.get('command')
    
    if not node_id or not command:
        return jsonify({"error": "node_id ve command parametreleri gerekli"}), 400
    
    # MQTT ile komutu gönder
    client.publish(MQTT_TOPIC_CONTROL, command)
    
    return jsonify({"status": "success", "message": f"Komut gönderildi: {command}"})

if __name__ == "__main__":
    # Veritabanını hazırla
    init_db()
    
    # MQTT istemcisini başlat
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        logger.info("MQTT istemcisi başlatıldı")
    except Exception as e:
        logger.error(f"MQTT bağlantı hatası: {e}")
    
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=5000, debug=True)