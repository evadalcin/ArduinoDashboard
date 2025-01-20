#include <TinyDHT.h>
#include <ArduinoJson.h>
#include <HCSR04.h>

#define DHT_SENSOR_TYPE DHT11
int pinDHT = 2;
int pirPin = 7;
int pirValue;
int sensorPin = A0;
int digitalSensorPin = 3;
int soundValue = 0;
int photoPin = A1;
int lightValue = 0;
int ledPin = 10;

DHT dht(pinDHT, DHT11);
HCSR04 hc(9, 8); // trig pin 9, echo pin 8

void setup() {
  Serial.begin(9600);
  pinMode(pirPin, INPUT);
  pinMode(ledPin, OUTPUT);
  dht.begin();
}

void loop() {
  pirValue = digitalRead(pirPin);
  soundValue = analogRead(sensorPin);
  lightValue = analogRead(photoPin);
  int8_t humidity = dht.readHumidity();
  int16_t temperature = dht.readTemperature(0);
  float distance = hc.dist(); // lettura distanza in cm

  StaticJsonDocument<256> doc;
  doc["temperatura"] = temperature;
  doc["umidita"] = humidity;
  doc["movimento"] = (pirValue == HIGH ? "Rilevato" : "Non rilevato");
  doc["suono"] = soundValue;
  doc["luce"] = lightValue;
  doc["distanza"] = distance;

  if (pirValue == HIGH) {
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }

  serializeJson(doc, Serial);
  Serial.println();
  delay (100);
}
