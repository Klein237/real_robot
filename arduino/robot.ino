// for the robot.ino file. Do not suggest code that has been deleted.

 /* After running the code, smart car can be controlled with a xbox controller throught a serial
 * ros2 bridge. The xbox controller should be connected to a pc by Bleutooth ou wire
 */

// robot_serial.ino
// Receives serial commands from PC and drives motors
// Format received: "L:200,R:-180\n"

#define speedPinR        9      //  RIGHT PWM pin connect MODEL-X ENA
#define RightDirectPin1  12     //Right Motor direction pin 1 to MODEL-X IN1 
#define RightDirectPin2  11     //Right Motor direction pin 2 to MODEL-X IN2
#define speedPinL        6      // Left PWM pin connect MODEL-X ENB
#define LeftDirectPin1   7      //Left Motor direction pin 1 to MODEL-X IN3 
#define LeftDirectPin2   8      //Left Motor direction pin 1 to MODEL-X IN4 

void setup() {
  pinMode(RightDirectPin1, OUTPUT);
  pinMode(RightDirectPin2, OUTPUT);
  pinMode(speedPinL,       OUTPUT);
  pinMode(LeftDirectPin1,  OUTPUT);
  pinMode(LeftDirectPin2,  OUTPUT);
  pinMode(speedPinR,       OUTPUT);

  Serial.begin(115200);
  stopMotors();
}

void stopMotors() {
  digitalWrite(RightDirectPin1, LOW);
  digitalWrite(RightDirectPin2, LOW);
  digitalWrite(LeftDirectPin1,  LOW);
  digitalWrite(LeftDirectPin2,  LOW);
  analogWrite(speedPinL, 0);
  analogWrite(speedPinR, 0);
}

void setMotors(int l, int r) {
  // Left motor
  digitalWrite(LeftDirectPin1, l > 0 ? HIGH : LOW);
  digitalWrite(LeftDirectPin2, l > 0 ? LOW  : HIGH);
  analogWrite(speedPinL, abs(l));

  // Right motor
  digitalWrite(RightDirectPin1, r > 0 ? HIGH : LOW);
  digitalWrite(RightDirectPin2, r > 0 ? LOW  : HIGH);
  analogWrite(speedPinR, abs(r));
}

void loop() {
  // Safety: stop if no command received for 500ms
  static unsigned long lastCmd = 0;
  if (millis() - lastCmd > 500) {
    stopMotors();
  }

  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    // Expected format: "L:200,R:-180"
    int commaIdx = data.indexOf(',');
    if (commaIdx > 0) {
      int l = data.substring(2, commaIdx).toInt();
      int r = data.substring(commaIdx + 3).toInt();
      setMotors(l, r);
      lastCmd = millis();
    }
  }
}