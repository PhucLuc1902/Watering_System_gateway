# Smart Irrigation Gateway — Setup & Execution Guide

Hướng dẫn cài đặt và vận hành đầy đủ cho hệ thống tưới cây thông minh gồm hai thành phần:
- **ESP32-S3** chạy firmware `main.cpp` (đọc cảm biến, điều khiển relay)
- **Python Gateway** chạy `gateway_v3_no_pump_cmd.py` (trung gian giữa ESP32 và backend/Adafruit)

---

## Cấu trúc file cốt lõi
Để dễ dàng theo dõi, dưới đây là các file chính cấu thành hệ thống:
- `src/main.cpp`: Mã nguồn C++ chạy trên ESP32 (quản lý cảm biến, bơm, LCD).
- `gateway_v3_no_pump_cmd.py`: Script Python trung tâm (đọc Serial từ ESP32, xử lý logic tưới, gọi Backend API và Adafruit IO).
- `platformio.ini`: Cấu hình môi trường biên dịch, định nghĩa board ESP32 và các thư viện C++.
- `.env.example`: File mẫu chứa các biến môi trường cấu hình hệ thống.

---

## Mục lục

1. [Yêu cầu hệ thống và phần cứng](#1-yêu-cầu-hệ-thống-và-phần-cứng)
2. [Cài đặt VS Code + PlatformIO (ESP32)](#2-cài-đặt-vs-code--platformio-esp32)
3. [Nạp firmware lên ESP32](#3-nạp-firmware-lên-esp32)
4. [Cài đặt Python + Gateway](#4-cài-đặt-python--gateway)
5. [Cấu hình file `.env`](#5-cấu-hình-file-env)
6. [Chạy và Dừng Gateway](#6-chạy-và-dừng-gateway)
7. [Kiểm tra hệ thống](#7-kiểm-tra-hệ-thống)
8. [Các lỗi thường gặp](#8-các-lỗi-thường-gặp)

---

## 1. Yêu cầu hệ thống và phần cứng

### 1.1 Yêu cầu phần mềm
- **Hệ điều hành:** Windows 10/11 (khuyên dùng), macOS, hoặc Linux.
- **Công cụ lập trình:** Visual Studio Code, PlatformIO IDE.
- **Môi trường:** Python 3.11+.

### 1.2 Yêu cầu phần cứng

| Thiết bị | Thông số |
|---|---|
| Vi điều khiển | ESP32-S3 DevKitC-1 |
| Cảm biến nhiệt độ/độ ẩm | DHT11 (chân GPIO **3**) |
| Cảm biến độ ẩm đất | Capacitive (chân GPIO **14**, ADC 12-bit) |
| Relay | Active-LOW (chân GPIO **4**) |
| LCD | I2C 16x2, địa chỉ `0x27` (SDA: GPIO **8**, SCL: GPIO **9**) |
| LED cảnh báo | GPIO **20** |
| Cáp | USB-C (kết nối ESP32 với máy tính) |

> **Lưu ý về relay:** Firmware mặc định dùng relay **Active-LOW** (`RELAY_ACTIVE_LOW 1`). Nếu relay của bạn là Active-HIGH, sửa dòng `#define RELAY_ACTIVE_LOW 1` thành `0` trong `src/main.cpp`.

---

## 2. Cài đặt VS Code + PlatformIO (ESP32)

### 2.1 Tải VS Code

Tải và cài đặt tại: **https://code.visualstudio.com/**

### 2.2 Cài Extension PlatformIO IDE

1. Mở VS Code → nhấn `Ctrl+Shift+X` để mở **Extensions**
2. Tìm kiếm: `PlatformIO IDE`
3. Chọn extension của **PlatformIO** → nhấn **Install**
4. Chờ cài xong, VS Code sẽ yêu cầu **Reload** → nhấn Reload

> Sau khi cài, icon con kiến 🐜 (PlatformIO) sẽ xuất hiện ở thanh bên trái VS Code.

### 2.3 Mở project

1. Nhấn icon PlatformIO → **Open Project**
2. Chọn thư mục `Watering system` (nơi chứa `platformio.ini`)
3. PlatformIO sẽ tự tải các thư viện trong `lib_deps` về:
   - `LiquidCrystal_I2C`
   - `Adafruit Unified Sensor`
   - `DHT sensor library`
   - `PubSubClient`

---

## 3. Nạp firmware lên ESP32

### 3.1 Cài driver USB cho ESP32-S3

ESP32-S3 dùng chip **USB-CDC** tích hợp. Windows cần driver để nhận ra cổng COM:

1. Cắm ESP32 vào máy tính
2. Mở **Device Manager** — nếu thấy `Unknown Device` hoặc `USB Serial Device` có dấu `!` → cần cài driver
3. Tải driver **CP210x** hoặc **CH340** (tùy board) tại:
   - Silicon Labs CP210x: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
   - CH340: https://www.wch-ic.com/downloads/CH341SER_EXE.html
4. Sau khi cài driver, rút và cắm lại cáp USB → kiểm tra lại Device Manager → **Ports (COM & LPT)**

> Nếu board ESP32-S3 DevKitC-1 gốc từ Espressif thì dùng USB-CDC native, không cần driver thêm — chỉ cần đúng Windows 10/11.

### 3.2 Kết nối và xác nhận cổng COM

- Cắm cáp USB-C vào ESP32 và máy tính
- Kiểm tra cổng COM: **Device Manager** → **Ports (COM & LPT)**
- Ghi nhớ cổng, ví dụ: `COM4`

### 3.3 Build & Upload

Trong VS Code với PlatformIO:

```
# Cách 1: Dùng thanh công cụ PlatformIO (biểu tượng ở dưới cùng VS Code)
→ Click ✓ (Build)    để biên dịch
→ Click → (Upload)   để nạp firmware

# Cách 2: Dùng PlatformIO Terminal
pio run --target upload
```

### 3.4 Mở Serial Monitor để kiểm tra

```
pio device monitor --baud 115200
```

Bạn sẽ thấy output dạng:
```
!TEMP=28.5;HUMI=65.0;SOIL=52;RAW=2100;PUMP=0;RELAY=1#
!TEMP=28.5;HUMI=65.0;SOIL=52;RAW=2100;PUMP=0;RELAY=1#
```

> Nếu thấy `DHT error` → kiểm tra lại dây nối cảm biến DHT11.

---

## 4. Cài đặt Python + Gateway

### 4.1 Tải Python

Tải Python **3.11 trở lên** tại: **https://www.python.org/downloads/**

> ⚠️ Khi cài, tick chọn **"Add Python to PATH"** trước khi nhấn Install.

Kiểm tra sau khi cài:
```powershell
python --version
# Python 3.11.x hoặc cao hơn
```

### 4.2 Cài các thư viện Python cần thiết

Mở terminal trong thư mục project và chạy:

```powershell
pip install pyserial requests python-dotenv Adafruit-IO
```

| Thư viện | Chức năng |
|---|---|
| `pyserial` | Đọc dữ liệu từ ESP32 qua cổng Serial (COM) |
| `requests` | Gọi REST API lên Backend |
| `python-dotenv` | Đọc file `.env` chứa thông tin bí mật |
| `Adafruit-IO` | Kết nối Adafruit IO để đẩy dữ liệu lên cloud |

---

## 5. Cấu hình file `.env`

Tạo file `.env` trong thư mục project (sao chép từ `.env.example`):

```powershell
copy .env.example .env
```

Sau đó mở `.env` và điền các giá trị thực:

```env
# =============================================
# ADAFRUIT IO — Bắt buộc
# =============================================
AIO_USERNAME=tên_người_dùng_adafruit_của_bạn
AIO_KEY=khóa_API_adafruit_của_bạn

# =============================================
# FEED NAMES — Giữ nguyên nếu dùng tên mặc định
# =============================================
FEED_TEMP=temperature
FEED_HUM=humidity
FEED_SOIL=soil
FEED_PUMP=pump
# FEED_PUMP_CMD: feed đọc lệnh BẬT/TẮT bơm từ người dùng (mặc định dùng chung FEED_PUMP)
FEED_PUMP_CMD=pump
# FEED_PUMP_STATE: feed gateway ghi trạng thái bơm thực tế lên (mặc định dùng chung FEED_PUMP)
FEED_PUMP_STATE=pump
# AIO_AUDIT_FEED_ENABLED: đặt 1 để đẩy audit log lên Adafruit (cẩn thận throttle)
AIO_AUDIT_FEED_ENABLED=0

# =============================================
# BACKEND API — Bắt buộc
# =============================================
API_BASE_URL=https://smart-irrigation-jet.vercel.app
ZONE_ID=uuid-của-zone-trong-database
API_TOKEN=token-xác-thực-backend-của-bạn

# =============================================
# SCHEDULE — Tùy chọn
# Nếu muốn dùng lịch cố định, điền SCHEDULE_ID
# =============================================
SCHEDULE_ID=uuid-của-schedule-trong-database

# =============================================
# SERIAL — Khớp với cổng COM của ESP32
# =============================================
SERIAL_PORT=COM4
SERIAL_BAUD=115200

# =============================================
# TIMING — Có thể giữ nguyên mặc định
# =============================================
CONFIG_REFRESH_SEC=15
SENSOR_SEND_INTERVAL_SEC=15
ALERT_INTERVAL_SEC=300
DEVICE_OFFLINE_SEC=30
# MANUAL_FEED_STALE_SEC: lệnh thủ công cũ hơn X giây sẽ bị bỏ qua (tránh lệnh cũ can thiệp lịch tự động)
MANUAL_FEED_STALE_SEC=120

# =============================================
# SOIL CALIBRATION — Điều chỉnh theo cảm biến thực tế
# SOIL_RAW_DRY: giá trị ADC khi đất khô hoàn toàn
# SOIL_RAW_WET: giá trị ADC khi đất ướt hoàn toàn
# =============================================
SOIL_RAW_DRY=4095
SOIL_RAW_WET=1200
COMPUTE_SOIL_FROM_RAW=1

# =============================================
# EMAIL CẢNH BÁO — Tùy chọn
# =============================================
GMAIL_SENDER=email_gửi@gmail.com
GMAIL_APP_PASSWORD=mật_khẩu_ứng_dụng_gmail
GMAIL_RECEIVER=email_nhận@gmail.com

# =============================================
# AI MODE — Tùy chọn
# =============================================
AI_LAT=10.7291
AI_LON=106.6984
AI_CALL_INTERVAL_SEC=3600
```

### Cách lấy các giá trị bí mật

| Giá trị | Cách lấy |
|---|---|
| `AIO_USERNAME` | Đăng nhập [io.adafruit.com](https://io.adafruit.com) → góc trên phải → tên người dùng |
| `AIO_KEY` | Adafruit IO → **My Key** (icon chìa khóa) → copy Active Key |
| `ZONE_ID` | Lấy từ dashboard Backend hoặc database của bạn (dạng UUID) |
| `API_TOKEN` | Lấy từ Backend — thường được tạo khi đăng ký tài khoản hoặc tạo zone |
| `SCHEDULE_ID` | Lấy từ Backend khi tạo lịch tưới trong web app |
| `GMAIL_APP_PASSWORD` | Google Account → Security → **App Passwords** (cần bật 2FA trước) |

> ⚠️ **Không được commit file `.env` lên git!** File `.gitignore` đã chặn sẵn.

---

## 6. Chạy và Dừng Gateway

### 6.1 Kiểm tra cổng Serial trước

Đảm bảo ESP32 đã được cắm và đúng cổng COM trong `.env`:

```powershell
# Kiểm tra các cổng COM đang hoạt động
python -c "import serial.tools.list_ports; [print(p) for p in serial.tools.list_ports.comports()]"
```

### 6.2 Chạy Gateway

```powershell
# Di chuyển vào thư mục project (thay đường dẫn cho đúng với máy bạn)
cd "<đường_dẫn_đến_thư_mục_Watering system>"
# Ví dụ:
# cd "C:\Users\TenBan\Documents\PlatformIO\Projects\Watering system"

# Chạy gateway
python gateway_v3_no_pump_cmd.py
```

### 6.3 Output bình thường khi gateway chạy thành công

```
Gateway started...
Overriding schedule with SCHEDULE_ID from env: 93cb9101-...
Zone config refreshed -> zone=Vườn nhà, mode=AUTO, min=40, max=80, slots=1
Sent time to ESP32: !TIME=1777049871#
Sent zone to ESP32: !ZONE=37baab23-...#
[SYSTEM] Local Time: 23:57 | Epoch: 1777049871
Temp: 28.5
Hum: 65.0
Soil: 52
Pump: 0
--------------
Sending to Adafruit... changed(TEMP,HUMI,SOIL)
Send OK (3 feed(s))
===============
```

### 6.4 Chạy ngầm (background) — tùy chọn

```powershell
# Chạy ẩn và lưu log ra file
Start-Process python -ArgumentList "gateway_v3_no_pump_cmd.py" -WindowStyle Hidden -RedirectStandardOutput "gateway.log" -RedirectStandardError "gateway_err.log"

# Xem log realtime
Get-Content gateway.log -Wait
```

### 6.5 Dừng Gateway (Shutdown)
Việc dừng Gateway đúng cách giúp giải phóng cổng COM, cho phép nạp lại code ESP32 nếu cần.

- **Nếu đang chạy trực tiếp trên Terminal:** Nhấn tổ hợp phím `Ctrl + C` để dừng.
- **Nếu đang chạy ngầm (background) trên Windows:**
  Mở PowerShell (Run as Administrator nếu cần) và chạy lệnh sau để kill tiến trình Python đang chiếm dụng:
  ```powershell
  Get-Process python | Stop-Process -Force
  ```
  *(Lưu ý: Lệnh này sẽ đóng toàn bộ các tiến trình Python đang chạy trên máy).*

---

## 7. Kiểm tra hệ thống

### 7.1 Checklist khởi động

- [ ] ESP32 đã được nạp firmware và đang gửi telemetry qua Serial
- [ ] File `.env` đã điền đầy đủ `AIO_USERNAME`, `AIO_KEY`, `ZONE_ID`, `API_TOKEN`
- [ ] `SERIAL_PORT` trong `.env` khớp với cổng COM thực tế của ESP32
- [ ] Gateway in ra `Zone config refreshed` mà không có lỗi
- [ ] Adafruit IO nhận được dữ liệu (kiểm tra tại [io.adafruit.com](https://io.adafruit.com))
- [ ] Backend không trả về lỗi `400 Bad Request`

### 7.2 Kiểm tra luồng dữ liệu

```
ESP32 (Serial) → Gateway (Python) → Adafruit IO (cloud)
                                  → Backend API (database)
```

### 7.3 Các mode hoạt động

| Mode | Mô tả |
|---|---|
| `MANUAL` | Người dùng bật/tắt bơm thủ công qua web hoặc Adafruit |
| `AUTO` | Gateway tự tưới khi đất khô dưới `min_soil`, dừng khi đạt điểm giữa `(min+max)/2` |
| `SCHEDULE` | Tưới theo lịch giờ/ngày thiết lập trên web |
| `AI` | Gọi API AI để đề xuất lịch tưới tối ưu mỗi giờ |

---

## 8. Các lỗi thường gặp

### `serialutil.SerialException: could not open port COM4`
**Nguyên nhân:** Sai cổng COM hoặc ESP32 chưa được kết nối.  
**Cách sửa:** Kiểm tra Device Manager → sửa `SERIAL_PORT` trong `.env`.

### `DHT error` trên Serial Monitor ESP32
**Nguyên nhân:** Dây nối cảm biến DHT11 bị lỏng hoặc đứt.  
**Cách sửa:** Kiểm tra lại dây nối chân DATA của DHT11 vào GPIO 3. Gateway sẽ tự động gửi cảnh báo `IRRIGATION_EVENT` lên audit log.

### `400 Client Error: Bad Request for url: .../api/alerts`
**Nguyên nhân:** Payload thiếu trường bắt buộc (thường là `zoneName`).  
**Cách sửa:** Đã được sửa trong phiên bản hiện tại của gateway. Kiểm tra `ZONE_ID` trong `.env` không có khoảng trắng thừa.

### `ThrottlingError` từ Adafruit
**Nguyên nhân:** Gửi dữ liệu quá nhanh (Adafruit free tier giới hạn 30 điểm/phút).  
**Cách sửa:** Tăng `SENSOR_SEND_INTERVAL_SEC` lên `15` hoặc `30` trong `.env`.

### `Failed to fetch zone devices: ...`
**Nguyên nhân:** `ZONE_ID` sai hoặc `API_TOKEN` hết hạn.  
**Cách sửa:** Kiểm tra lại `ZONE_ID` và `API_TOKEN` trong `.env`.

### Gateway không nhận lệnh thủ công từ web
**Nguyên nhân:** Lệnh cũ (stale) từ Adafruit feed đang bị hệ thống bỏ qua do cơ chế chống dao động.  
**Cách sửa:** Chờ 30 giây sau khi tưới tự động kết thúc rồi thử lại, hoặc giảm `MANUAL_FEED_STALE_SEC` trong `.env`.

### `ValueError: invalid literal for int() with base 10: ''` khi khởi động
**Nguyên nhân:** Biến `FORCE_SCHEDULE_DURATION_MIN` trong `.env` bị để trống.  
**Cách sửa:** Nếu không dùng local schedule, xóa hoàn toàn dòng đó khỏi `.env` hoặc đặt giá trị hợp lệ:
```env
# Nếu không dùng:
# FORCE_SCHEDULE_DURATION_MIN=
# Nếu dùng thì điền số phút cụ thể:
FORCE_SCHEDULE_DURATION_MIN=10
```

### Gateway throttle Adafruit liên tục dù `SENSOR_SEND_INTERVAL_SEC` đã cao
**Nguyên nhân:** `AIO_AUDIT_FEED_ENABLED=1` đang bật, mỗi sự kiện audit cũng tốn 1 data point.  
**Cách sửa:** Giữ `AIO_AUDIT_FEED_ENABLED=0` (mặc định) — audit log vẫn được gửi lên Backend API, chỉ không đẩy lên Adafruit feed.
