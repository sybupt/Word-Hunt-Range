#include <Arduino.h>
#include <BleMouse.h>
#include <Bounce2.h>
#include <MPU6050_light.h>
#include <Wire.h>

// ===== 引脚 =====
#define BUTTON_PIN 4
#define BATTERY_PIN 2

// ===== 电池参数 =====
#define ADC_CORRECTION 1.564f
#define BATTERY_MAX_V 2.50f
#define BATTERY_MIN_V 1.80f
#define ADC_REF_V 3.3f
#define ADC_RESOLUTION 4095.0f

// ===== 核心调参 =====
#define GAIN 0.25f
#define DEAD_ZONE 0.8f
#define SMOOTH_FACTOR 0.5f
#define INVERT_Y 1

// ===== 静止判定参数 =====
#define STILL_WIN 60
#define RANGE_THRESH 1.2f
#define ABS_THRESH 2.0f
#define STILL_COUNT_THRESH 80
#define MOTION_LOCK_COUNT 100
#define BIAS_ALPHA 0.008f
#define ACCUM_CLEAR_MS 1000

// ===== BLE发送参数 =====
/**
 * PENDING_LIMIT：pendingX/Y 的最大累积量
 * 防止BLE卡顿时 pending 无限增长导致鼠标瞬移
 * 200Hz * 127 * 0.25(gain) ≈ 理论最大速度，5000 足够安全
 */
#define PENDING_LIMIT 2000

/**
 * BLE_SEND_INTERVAL_MS：BLE发送任务的固定节拍（ms）
 * 必须 > 实际BLE连接间隔，设60ms对所有平台保守安全
 * Windows≈46ms / Mac≈30ms / Android≈11ms
 * 60ms是对Windows最保守的选择，改成45可以提升Mac/Android流畅度
 * 如果还有notify error就改成70
 */
#define BLE_SEND_INTERVAL_MS 60

// ============================================================
// 共享位移寄存器
// 传感器（Core1）原子累加，BLE任务（Core0）每帧取一包发送
// ============================================================
static volatile int pendingX = 0;
static volatile int pendingY = 0;
static portMUX_TYPE moveMux = portMUX_INITIALIZER_UNLOCKED;

static SemaphoreHandle_t bleSemaphore = nullptr;

BleMouse mouse("AirMouse", "ESP32", 100);
Bounce debouncer;
MPU6050 mpu(Wire);

unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL = 5;
unsigned long lastBattTime = 0;
const unsigned long BATT_INTERVAL = 30000;

float lastMouseX = 0, lastMouseY = 0;
float accumX = 0, accumY = 0;
float gyroX_bias = 0, gyroZ_bias = 0;

float gyroX_win[STILL_WIN];
float gyroZ_win[STILL_WIN];
int winIdx = 0;
bool winFull = false;

int stillCount = 0;
int motionLock = 0;
bool biasUpdateOK = false;

unsigned long stationaryConfirmedStart = 0;
bool isConfirmedStationary = false;
bool lastConn = false;

// 非阻塞日志
#define LOG_BUF_SIZE 160
static char logBuf[LOG_BUF_SIZE];
static bool logPending = false;
static unsigned long lastLogTime = 0;
const unsigned long LOG_INTERVAL = 500;

void scheduleLog(float rX, float rZ, float bX, float bZ,
                 float p, float y, int sc, int lk, int ok,
                 float aX, float aY, int mX, int mY,
                 int pX, int pY)
{
    if (!logPending) {
        snprintf(logBuf, LOG_BUF_SIZE,
                 "R(%.2f,%.2f) B(%.2f,%.2f) P(%.2f,%.2f) "
                 "s=%d lk=%d ok=%d ac=(%.2f,%.2f) mv=(%d,%d) pend=(%d,%d)",
                 rX, rZ, bX, bZ, p, y,
                 sc, lk, ok, aX, aY, mX, mY, pX, pY);
        logPending = true;
    }
}

void calibrateMPU();
uint8_t readBatteryLevel();
void reportBattery();
bool checkStill(float *bufX, float *bufZ, int n);

// ============================================================
// BLE发送任务（Core 0）
//
// ★ 修复ChatGPT指出的问题2：
//    不再用while循环一次清空，改为"每帧只发一包"
//    效果：大位移被平滑分摊到多个BLE帧，无突变，手感丝滑
//
// 节拍：BLE_SEND_INTERVAL_MS（60ms）
//    → 每帧最多发 ±127
//    → 1秒最多发 127 * (1000/60) ≈ 2116 单位
//    → 足够覆盖所有正常操作速度
// ============================================================
void bleTask(void *param)
{
    BleMouse *m = (BleMouse *)param;

    for (;;) {
        // 等BLE连接信号（断连时挂起，不空转耗CPU）
        xSemaphoreTake(bleSemaphore, portMAX_DELAY);
        xSemaphoreGive(bleSemaphore);

        if (!m->isConnected()) {
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

        // ★ 每帧只取一包（±127范围内）
        // pending里剩余的留到下一帧，天然平滑
        int8_t sx, sy;
        portENTER_CRITICAL(&moveMux);
        sx = (int8_t)constrain(pendingX, -127, 127);
        sy = (int8_t)constrain(pendingY, -127, 127);
        pendingX -= sx;
        pendingY -= sy;
        portEXIT_CRITICAL(&moveMux);

        if (sx != 0 || sy != 0) {
            m->move(sx, sy);
        }

        // 固定节拍等待，对齐BLE连接间隔
        vTaskDelay(pdMS_TO_TICKS(BLE_SEND_INTERVAL_MS));
    }
}

void setup()
{
    Serial.begin(115200);
    delay(1000);
    Serial.println("=== AirMouse (Final v3) ===");

    bleSemaphore = xSemaphoreCreateBinary();

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

    Serial.println("等待传感器稳定...");
    delay(1500);
    Serial.println("校准中，请保持静止并水平放置...");
    mpu.calcOffsets();
    delay(200);
    calibrateMPU();

    memset(gyroX_win, 0, sizeof(gyroX_win));
    memset(gyroZ_win, 0, sizeof(gyroZ_win));

    mouse.begin();

    xTaskCreatePinnedToCore(
        bleTask, "bleTask", 4096, &mouse, 1, nullptr, 0);

    Serial.println("Init Done.");
}

void calibrateMPU()
{
    float sumX = 0, sumZ = 0;
    for (int i = 0; i < 500; i++) {
        mpu.update();
        sumX += mpu.getGyroX();
        sumZ += mpu.getGyroZ();
        delay(2);
    }
    gyroX_bias = sumX / 500.0f;
    gyroZ_bias = sumZ / 500.0f;
    Serial.printf("偏置: X=%.3f  Z=%.3f\n", gyroX_bias, gyroZ_bias);
    if (fabsf(gyroX_bias) > 2.0f || fabsf(gyroZ_bias) > 2.0f) {
        Serial.println("警告：偏置过大！请水平静止放置后重启。");
    }
}

uint8_t readBatteryLevel()
{
    long sum = 0;
    for (int i = 0; i < 16; i++) {
        sum += analogRead(BATTERY_PIN);
        delay(1);
    }
    float adcVal = sum / 16.0f;
    if (adcVal < 100)
        return 255;
    float v = (adcVal / ADC_RESOLUTION) * ADC_REF_V * ADC_CORRECTION;
    float pct = (v - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V) * 100.0f;
    pct = constrain(pct, 0.0f, 100.0f);
    Serial.printf("[BATT] %.2fV (%d%%)\n", v, (int)pct);
    return (uint8_t)pct;
}

void reportBattery()
{
    uint8_t batt = readBatteryLevel();
    if (batt != 255 && mouse.isConnected()) {
        mouse.setBatteryLevel(batt);
        lastBattTime = millis();
    }
}

bool checkStill(float *bufX, float *bufZ, int n)
{
    if (n < 10)
        return false;
    float mnX = bufX[0], mxX = bufX[0], sumX = 0;
    float mnZ = bufZ[0], mxZ = bufZ[0], sumZ = 0;
    for (int i = 0; i < n; i++) {
        if (bufX[i] < mnX)
            mnX = bufX[i];
        if (bufX[i] > mxX)
            mxX = bufX[i];
        if (bufZ[i] < mnZ)
            mnZ = bufZ[i];
        if (bufZ[i] > mxZ)
            mxZ = bufZ[i];
        sumX += bufX[i];
        sumZ += bufZ[i];
    }
    bool rangeOK = (mxX - mnX < RANGE_THRESH) && (mxZ - mnZ < RANGE_THRESH);
    bool absOK = (fabsf(sumX / n) < ABS_THRESH) && (fabsf(sumZ / n) < ABS_THRESH);
    return rangeOK && absOK;
}

void loop()
{
    unsigned long now = millis();
    bool nowConn = mouse.isConnected();

    // 非阻塞日志
    if (logPending && (now - lastLogTime >= LOG_INTERVAL)) {
        Serial.println(logBuf);
        logPending = false;
        lastLogTime = now;
    }

    if (nowConn != lastConn) {
        lastConn = nowConn;
        if (nowConn) {
            Serial.println("[BLE] Connected");
            // 连接瞬间清空所有残留，防飞鼠
            portENTER_CRITICAL(&moveMux);
            pendingX = 0;
            pendingY = 0;
            portEXIT_CRITICAL(&moveMux);
            accumX = 0;
            accumY = 0;
            lastMouseX = 0;
            lastMouseY = 0;
            delay(300);
            reportBattery();
            xSemaphoreGive(bleSemaphore);
        } else {
            Serial.println("[BLE] Disconnected");
            lastMouseX = lastMouseY = 0;
        }
    }
    if (!nowConn) {
        lastMouseX = lastMouseY = 0;
    }
    if (nowConn && (now - lastBattTime > BATT_INTERVAL)) {
        reportBattery();
    }

    // ── 200Hz 传感器读取（Core 1）──
    if (now - lastReadTime >= READ_INTERVAL) {
        lastReadTime = now;
        mpu.update();

        float rawX = mpu.getGyroX();
        float rawZ = mpu.getGyroZ();

        gyroX_win[winIdx] = rawX;
        gyroZ_win[winIdx] = rawZ;
        winIdx = (winIdx + 1) % STILL_WIN;
        if (winIdx == 0)
            winFull = true;
        int checkN = winFull ? STILL_WIN : winIdx;

        bool rawStill = checkStill(gyroX_win, gyroZ_win, checkN);

        if (rawStill) {
            if (stillCount < STILL_COUNT_THRESH)
                stillCount++;
        } else {
            if (stillCount > 0)
                motionLock = MOTION_LOCK_COUNT;
            stillCount = 0;
        }
        if (motionLock > 0)
            motionLock--;

        biasUpdateOK = (stillCount >= STILL_COUNT_THRESH) && (motionLock == 0);

        if (biasUpdateOK) {
            gyroX_bias = gyroX_bias * (1.0f - BIAS_ALPHA) + rawX * BIAS_ALPHA;
            gyroZ_bias = gyroZ_bias * (1.0f - BIAS_ALPHA) + rawZ * BIAS_ALPHA;
            if (!isConfirmedStationary) {
                isConfirmedStationary = true;
                stationaryConfirmedStart = now;
            }
            if (now - stationaryConfirmedStart > ACCUM_CLEAR_MS) {
                accumX = 0;
                accumY = 0;
            }
        } else {
            isConfirmedStationary = false;
        }

        float pitch = rawX - gyroX_bias;
        float yaw = rawZ - gyroZ_bias;
        if (fabsf(pitch) < DEAD_ZONE)
            pitch = 0;
        if (fabsf(yaw) < DEAD_ZONE)
            yaw = 0;

        float vX = -yaw * GAIN;
        float vY = pitch * GAIN * (INVERT_Y ? -1.0f : 1.0f);

        float smX = lastMouseX * (1.0f - SMOOTH_FACTOR) + vX * SMOOTH_FACTOR;
        float smY = lastMouseY * (1.0f - SMOOTH_FACTOR) + vY * SMOOTH_FACTOR;
        lastMouseX = smX;
        lastMouseY = smY;

        accumX += smX;
        accumY += smY;
        int moveX = (int)accumX;
        int moveY = (int)accumY;
        accumX -= moveX;
        accumY -= moveY;

        // ★ 修复ChatGPT指出的问题1：加限幅保险丝
        // pending超过PENDING_LIMIT说明BLE严重卡顿
        // 截断而不是丢弃：超出部分被抛弃，但不会归零
        if (moveX != 0 || moveY != 0) {
            portENTER_CRITICAL(&moveMux);
            pendingX = constrain(pendingX + moveX, -PENDING_LIMIT, PENDING_LIMIT);
            pendingY = constrain(pendingY + moveY, -PENDING_LIMIT, PENDING_LIMIT);
            portEXIT_CRITICAL(&moveMux);
        }

        // 读取当前pending用于日志（不加锁，仅供参考）
        int lpx = pendingX, lpy = pendingY;
        scheduleLog(rawX, rawZ, gyroX_bias, gyroZ_bias,
                    pitch, yaw, stillCount, motionLock, (int)biasUpdateOK,
                    accumX, accumY, moveX, moveY, lpx, lpy);
    }

    // ── 按键 ──
    debouncer.update();
    if (debouncer.fell()) {
        if (mouse.isConnected())
            mouse.press(MOUSE_LEFT);
        Serial.println("BTN DOWN");
    }
    if (debouncer.rose()) {
        if (mouse.isConnected())
            mouse.release(MOUSE_LEFT);
        Serial.println("BTN UP");
    }

    delay(1);
}