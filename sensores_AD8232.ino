// Pines de salida analógica de cada AD8232
const int ecgPin1 = A0; // AD8232 #1
const int ecgPin2 = A1; // AD8232 #2
const int ecgPin3 = A2; // AD8232 #3

// Pines Lead-Off (opcional)
const int loPlus1  = 2;
const int loMinus1 = 3;
const int loPlus2  = 4;
const int loMinus2 = 5;
const int loPlus3  = 6;
const int loMinus3 = 7;

void setup() {
  Serial.begin(115200); // Velocidad alta para ver bien la señal

  pinMode(loPlus1,  INPUT);
  pinMode(loMinus1, INPUT);
  pinMode(loPlus2,  INPUT);
  pinMode(loMinus2, INPUT);
  pinMode(loPlus3,  INPUT);
  pinMode(loMinus3, INPUT);
}

void loop() {
  // Lecturas analógicas
  int ecg1 = analogRead(ecgPin1);
  int ecg2 = analogRead(ecgPin2);
  int ecg3 = analogRead(ecgPin3);

  // Estado de electrodos (0 = conectados, 1 = desconectados)
  bool leadOff1 = digitalRead(loPlus1) || digitalRead(loMinus1);
  bool leadOff2 = digitalRead(loPlus2) || digitalRead(loMinus2);
  bool leadOff3 = digitalRead(loPlus3) || digitalRead(loMinus3);

  // Mostrar datos
  Serial.print(ecg1);
  Serial.print(",");
  Serial.print(leadOff1);
  Serial.print(",");
  Serial.print(ecg2);
  Serial.print(",");
  Serial.print(leadOff2);
  Serial.print(ecg3);
  Serial.print(",");
  Serial.println(leadOff3);


  delay(2); // ~500 Hz de muestreo aprox.
}
