#include <WiFi.h>
#include <FirebaseESP32.h>

// ======================= WIFI CONFIG =========================
#define WIFI_SSID "YOUR_WIFI_NAME"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// ======================= FIREBASE CONFIG =====================
#define API_KEY "YOUR_FIREBASE_API_KEY"
#define DATABASE_URL "YOUR_FIREBASE_DATABASE_URL"

// Firebase auth
#define USER_EMAIL "YOUR_FIREBASE_EMAIL"
#define USER_PASSWORD "YOUR_FIREBASE_PASSWORD"

// Firebase objects
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// ======================= PINS ===============================
#define Wifi_LED 2

// Left Motor
#define IN1 13
#define IN2 12

// Right Motor
#define IN3 14
#define IN4 27

// ======================= ROBOT PARAMS =======================
#define WHEEL_RADIUS_CM 10.0
#define MOTOR_RPM 45.0
#define MOVE_TIME_SEC 4.0

float position_cm = 0.0;

// ======================= SETUP ===============================
void setup() {

  Serial.begin(115200);
  Serial.println("\nESP32 Firebase Motor Control");

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(Wifi_LED, OUTPUT);

  stp();

  // WiFi Connection
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(Wifi_LED, LOW);
    delay(250);
    digitalWrite(Wifi_LED, HIGH);
    delay(250);
  }

  digitalWrite(Wifi_LED, HIGH);

  Serial.println("\nWiFi Connected");
  Serial.println(WiFi.localIP());

  // Firebase Configuration
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  // Initialize Firebase values
  Firebase.RTDB.setInt(&fbdo, "/action", 0);
  Firebase.RTDB.setInt(&fbdo, "/detection", 1);
  Firebase.RTDB.setFloat(&fbdo, "/position_cm", position_cm);

  Serial.println("Firebase Connected");
}

// ======================= LOOP ================================
void loop() {

  if (!Firebase.RTDB.getInt(&fbdo, "/action")) {
    Serial.println(fbdo.errorReason());
    delay(500);
    return;
  }

  int action = fbdo.intData();

  Serial.print("Action received: ");
  Serial.println(action);

  switch (action) {

    case 0:
      stp();
      break;

    case 1: {

      Serial.println("Moving Forward");

      fwd();

      delay(MOVE_TIME_SEC * 1000);

      stp();

      // Distance Calculation
      float circumference = 2 * 3.1416 * WHEEL_RADIUS_CM;
      float speed_cm_sec = circumference * (MOTOR_RPM / 60.0);
      float distance = speed_cm_sec * MOVE_TIME_SEC;

      position_cm += distance;

      Firebase.RTDB.setFloat(&fbdo, "/position_cm", position_cm);
      Firebase.RTDB.setInt(&fbdo, "/detection", 1);
      Firebase.RTDB.setInt(&fbdo, "/action", 0);

      Serial.print("Distance updated: ");
      Serial.println(position_cm);

      break;
    }

    case 2:
      bwd();
      break;

    case 3:
      leftTurn();
      break;

    case 4:
      rightTurn();
      break;

    default:
      stp();
      break;
  }

  delay(300);
}

// ======================= MOTOR FUNCTIONS =====================

// Stop Motors
void stp() {

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  Serial.println("STOP");
}

// Move Forward
void fwd() {

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  Serial.println("FORWARD");
}

// Move Backward
void bwd() {

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  Serial.println("BACKWARD");
}

// Turn Left
void leftTurn() {

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  Serial.println("LEFT TURN");
}

// Turn Right
void rightTurn() {

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  Serial.println("RIGHT TURN");
}