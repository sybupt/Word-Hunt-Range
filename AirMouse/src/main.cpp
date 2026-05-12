#include <Arduino.h>
#include <BleMouse.h>
#include <Bounce2.h>
#include <MPU6050_light.h>
#include <Wire.h>

// ===== 引脚 =====
#define BUTTON_PIN 4
#define BATTERY_PIN 2

// ===== 电池参数 =====
// 你已用降压器，满电输出2.5V到D2
// ADC_CORRECTION = 万用表实测mV / ADC计算mV = 2500 / 1598
#define ADC_CORRECTION 1.564f // 根据你实测校准
#define BATTERY_MAX_V 2.50f   // 满电时D2万用表实测值
#define BATTERY_MIN_V 1.80f   // ← 没电时估算值，之后测到了改这里
#define ADC_REF_V 3.3f
#define ADC_RESOLUTION 4095.0f

// ===== 核心调参 =====
#define GAIN 0.25f
#define DEAD_ZONE 0.8f
#define SMOOTH_FACTOR 0.5f
#define INVERT_Y 1

#define DEBUG 0
#if DEBUG
#define LOG(...) Serial.printf(__VA_ARGS__)
#else
#define LOG(...)
#endif

BleMouse mouse("AirMouse", "ESP32", 100);
Bounce debouncer;
MPU6050 mpu(Wire);

unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL = 5;

unsigned long lastSendTime = 0;
const int SEND_INTERVAL = 10;

unsigned long lastBattTime = 0;
const unsigned long BATT_INTERVAL = 30000;

float lastMouseX = 0, lastMouseY = 0;
float accumX = 0, accumY = 0;

float gyroX_bias = 0, gyroZ_bias = 0;

unsigned long stationaryStart = 0;
bool isStationary = false;

bool lastConn = false;

void calibrateMPU();
uint8_t readBatteryLevel();
void reportBattery();

// ==================== setup ====================
void setup()
{
    Serial.begin(115200);
    delay(500);
    Serial.println("=== AirMouse Start ===");

    pinMode(BUTTON_PIN, INPUT_PULLUP);
    debouncer.attach(BUTTON_PIN);
    debouncer.interval(10);

    pinMode(BATTERY_PIN, INPUT);
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    Wire.begin();
    Wire.setClock(400000);

    if (mpu.begin() != 0) {
        Serial.println("MPU6050 ERROR!");
        while (1)
            delay(10);
    }

    mpu.calcOffsets();
    delay(500);
    calibrateMPU();

    Serial.println("MPU 校准完成");

    mouse.begin();
    Serial.println("BLE Mouse Started");
}

// ==================== 校准 ====================
void calibrateMPU()
{
    float sumX = 0, sumZ = 0;
    Serial.println("校准中，请不要移动...");

    for (int i = 0; i < 500; i++) {
        mpu.update();
        sumX += mpu.getGyroX();
        sumZ += mpu.getGyroZ();
        delay(2);
    }

    gyroX_bias = sumX / 500;
    gyroZ_bias = sumZ / 500;
    Serial.printf("偏置: X=%.3f  Z=%.3f\n", gyroX_bias, gyroZ_bias);
}

// ==================== 读取电量 ====================
uint8_t readBatteryLevel()
{
    // ADC=0 说明引脚悬空或BLE干扰，直接跳过
    long sum = 0;
    for (int i = 0; i < 32; i++) {
        sum += analogRead(BATTERY_PIN);
        delay(2);
    }
    float adcVal = sum / 32.0f;

    if (adcVal < 100) {
        Serial.println("[BATT] ADC异常（悬空或BLE干扰），跳过本次读取");
        return 255; // 255 = 无效标记，调用方忽略
    }

    float adcVoltage = (adcVal / ADC_RESOLUTION) * ADC_REF_V;
    float realVoltage = adcVoltage * ADC_CORRECTION;

    float pct = (realVoltage - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V) * 100.0f;
    pct = constrain(pct, 0.0f, 100.0f);

    Serial.printf("[BATT] ADC=%.0f  Vadc=%.3fV  Vreal=%.3fV  Level=%d%%\n",
                  adcVal, adcVoltage, realVoltage, (int)pct);

    return (uint8_t)pct;
}

// ==================== 上报电量 ====================
void reportBattery()
{
    uint8_t batt = readBatteryLevel();
    if (batt == 255)
        return; // 无效读数，不上报

    mouse.setBatteryLevel(batt);
    lastBattTime = millis();
}

// ==================== loop ====================
void loop()
{
    unsigned long now = millis();
    bool nowConn = mouse.isConnected();

    // ===== 连接状态变化 =====
    if (nowConn != lastConn) {
        lastConn = nowConn;
        if (nowConn) {
            Serial.println("[BLE] Connected");
            delay(300);      // 等BLE稳定再读ADC
            reportBattery(); // 连接后立即上报一次，不用等30秒
        } else {
            Serial.println("[BLE] Disconnected -> Restart");
            delay(500);
            esp_restart();
        }
    }

    // ===== 断开时清零累积 =====
    if (!nowConn) {
        accumX = 0;
        accumY = 0;
    }

    // ===== 定时上报电量 =====
    if (nowConn && (now - lastBattTime > BATT_INTERVAL)) {
        reportBattery();
    }

    // ===== 读取传感器 =====
    if (now - lastReadTime >= READ_INTERVAL) {
        lastReadTime = now;

        mpu.update();

        float rawGyroX = mpu.getGyroX();
        float rawGyroZ = mpu.getGyroZ();

        float pitch = rawGyroX - gyroX_bias;
        float yaw = rawGyroZ - gyroZ_bias;

        // 静止检测
        if (abs(pitch) < 0.5f && abs(yaw) < 0.5f) {
            if (!isStationary) {
                stationaryStart = now;
                isStationary = true;
            }
        } else {
            isStationary = false;
        }

        // 动态校准（静止超过2秒）
        if (isStationary && (now - stationaryStart > 2000)) {
            gyroX_bias = gyroX_bias * 0.999f + rawGyroX * 0.001f;
            gyroZ_bias = gyroZ_bias * 0.999f + rawGyroZ * 0.001f;
        }

        // 死区
        if (abs(pitch) < DEAD_ZONE)
            pitch = 0;
        if (abs(yaw) < DEAD_ZONE)
            yaw = 0;

        // 映射（左右反向加负号，如反了去掉负号）
        float rawX = -yaw * GAIN;
        float rawY = pitch * GAIN * (INVERT_Y ? -1 : 1);

        // 平滑
        float smoothX = lastMouseX * (1 - SMOOTH_FACTOR) + rawX * SMOOTH_FACTOR;
        float smoothY = lastMouseY * (1 - SMOOTH_FACTOR) + rawY * SMOOTH_FACTOR;
        lastMouseX = smoothX;
        lastMouseY = smoothY;

        // 累积取整
        accumX += smoothX;
        accumY += smoothY;
        int moveX = (int)accumX;
        int moveY = (int)accumY;
        accumX -= moveX;
        accumY -= moveY;

        // BLE发送
        if (nowConn && (now - lastSendTime > SEND_INTERVAL)) {
            lastSendTime = now;
            if (moveX != 0 || moveY != 0) {
                mouse.move(moveX, moveY);
            }
        }
    }

    // ===== 按钮 =====
    debouncer.update();

    if (debouncer.fell()) {
        Serial.println("BTN DOWN");
        if (mouse.isConnected())
            mouse.press(MOUSE_LEFT);
    }
    if (debouncer.rose()) {
        Serial.println("BTN UP");
        if (mouse.isConnected())
            mouse.release(MOUSE_LEFT);
    }

    delay(1);
}