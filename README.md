# Sensor Dashboard 

## Descrizione
Sensor Dashboard è un'applicazione web per il monitoraggio in tempo reale di sensori ambientali Arduino.
Il sistema utilizza un Arduino con vari sensori per raccogliere dati ambientali e li visualizza in modo interattivo.

## Componenti Hardware 
- Arduino (UNO o compatibile)
- Sensore DHT22 (temperatura e umidità)
- Sensore PIR (rilevamento movimento)
- Sensore sonoro
- Fotoresistore
- Sensore ultrasonico HC-SR04
- Breadboard e cavi di collegamento


### Librerie Arduino 
```cpp
- TinyDHT
- ArduinoJson
- HCSR04
```

### Librerie Python 
```bash
pip install flask flask-cors pymongo pyserial
```

## Funzionalità
- **Monitoraggio in Tempo Reale**: Visualizzazione continua dei dati dei sensori
- **Controllo Sensori**: Attivazione/disattivazione individuale dei sensori
- **Visualizzazione Dinamica**: Rappresentazione grafica animata dei dati
- **Gestione Errori**: Sistema robusto di gestione degli errori e riconnessione automatica

### Backend (Python/Flask)
- Server web Flask con supporto CORS
- Comunicazione seriale con Arduino
- Archiviazione dati su MongoDB
- API RESTful per la gestione dei dati e delle impostazioni

### Frontend (HTML/JavaScript)
- Visualizzazione realizzata con p5.js
- Aggiornamento dati in tempo reale

### Arduino
- Lettura periodica dei sensori
- Serializzazione JSON dei dati
- Gestione della comunicazione seriale

## Monitoraggio dei Sensori
- **Temperatura**: 0-50°C
- **Umidità**: 0-100%
- **Movimento**: Rilevato/Non rilevato
- **Suono**: Livello 0-1023
- **Luce**: Livello 0-1023
- **Distanza**: 0-400cm

## Credits : http://www.generative-gestaltung.de/2/sketches/?01_P/P_2_1_1_01

## Licenza
Questo progetto è distribuito con licenza MIT.
