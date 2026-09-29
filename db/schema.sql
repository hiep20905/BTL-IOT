-- =====================================================================
--  CƠ SỞ DỮ LIỆU HỆ THỐNG IoT (MQTT + ESP32 + Web Dashboard)
--  Bám theo CHƯƠNG 3 - THIẾT KẾ CƠ SỞ DỮ LIỆU của tài liệu SRS
--  SV: B23DCAT096 - Đàm Lê Đức Hiệp
--
--  Chạy:  mysql -u root -p < db/schema.sql
-- =====================================================================

DROP DATABASE IF EXISTS iot_db;
CREATE DATABASE iot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE iot_db;

-- ---------------------------------------------------------------------
-- 3.1 Bảng User - thông tin tài khoản người dùng
-- ---------------------------------------------------------------------
CREATE TABLE `User` (
  `user_id`    INT           NOT NULL AUTO_INCREMENT COMMENT 'Mã định danh duy nhất của người dùng',
  `username`   VARCHAR(50)   NOT NULL                COMMENT 'Tên đăng nhập hệ thống',
  `password`   VARCHAR(255)  NOT NULL                COMMENT 'Mật khẩu tài khoản (lưu dạng hash bcrypt)',
  -- Ba cột dưới phục vụ endpoint GET api/users/me (mục 4.3.3.g) và trang Profile
  `full_name`  VARCHAR(100)  NULL                    COMMENT 'Họ và tên hiển thị',
  `student_id` VARCHAR(20)   NULL                    COMMENT 'Mã sinh viên',
  `class`      VARCHAR(50)   NULL                    COMMENT 'Lớp',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uq_user_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3.2 Bảng Device - các thiết bị nhận lệnh điều khiển (đèn, quạt)
-- ---------------------------------------------------------------------
CREATE TABLE `Device` (
  `device_id`   INT          NOT NULL AUTO_INCREMENT COMMENT 'Mã định danh duy nhất của thiết bị',
  `device_name` VARCHAR(100) NOT NULL                COMMENT 'Tên gọi của thiết bị (vd: Đèn, Quạt)',
  `device_type` VARCHAR(50)  NOT NULL                COMMENT 'Chủng loại thiết bị (LED, Fan)',
  `is_active`   BOOLEAN      NOT NULL DEFAULT FALSE  COMMENT 'Trạng thái hoạt động (TRUE = ON, FALSE = OFF)',
  `last_active` DATETIME     NULL                    COMMENT 'Thời điểm gần nhất thiết bị gửi tín hiệu về hệ thống',
  PRIMARY KEY (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3.3 Bảng Action - lịch sử lệnh điều khiển người dùng gửi tới thiết bị
-- ---------------------------------------------------------------------
CREATE TABLE `Action` (
  `action_id`   INT         NOT NULL AUTO_INCREMENT COMMENT 'Mã định danh lịch sử thao tác',
  `user_id`     INT         NOT NULL                COMMENT 'FK -> User(user_id): ai thực hiện thao tác',
  `device_id`   INT         NOT NULL                COMMENT 'FK -> Device(device_id): tác động lên thiết bị nào',
  `action_type` VARCHAR(50) NOT NULL                COMMENT 'Loại lệnh điều khiển (ON, OFF)',
  `status`      VARCHAR(50) NOT NULL DEFAULT 'PENDING' COMMENT 'Kết quả thực thi (PENDING, SUCCESS, TIMEOUT)',
  `created_at`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm phát sinh lệnh điều khiển',
  PRIMARY KEY (`action_id`),
  KEY `idx_action_device_time` (`device_id`, `created_at`),
  KEY `idx_action_status`      (`status`),
  CONSTRAINT `fk_action_user`   FOREIGN KEY (`user_id`)   REFERENCES `User`(`user_id`),
  CONSTRAINT `fk_action_device` FOREIGN KEY (`device_id`) REFERENCES `Device`(`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3.4 Bảng Sensor - danh mục các loại cảm biến
-- ---------------------------------------------------------------------
CREATE TABLE `Sensor` (
  `sensor_id`   INT          NOT NULL AUTO_INCREMENT COMMENT 'Mã định danh duy nhất của cảm biến',
  `sensor_name` VARCHAR(100) NOT NULL                COMMENT 'Tên cảm biến (vd: DHT11, LDR)',
  `sensor_type` VARCHAR(50)  NOT NULL                COMMENT 'Loại cảm biến (Nhiệt độ, Độ ẩm, Ánh sáng)',
  PRIMARY KEY (`sensor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3.5 Bảng Data_sensor - chuỗi dữ liệu đo theo thời gian
-- ---------------------------------------------------------------------
CREATE TABLE `Data_sensor` (
  `data_id`     INT      NOT NULL AUTO_INCREMENT COMMENT 'Mã định danh bản ghi dữ liệu',
  `sensor_id`   INT      NOT NULL                COMMENT 'FK -> Sensor(sensor_id): giá trị thuộc cảm biến nào',
  `value`       FLOAT    NOT NULL                COMMENT 'Giá trị số liệu đo được từ cảm biến',
  `recorded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm ghi nhận giá trị đo',
  PRIMARY KEY (`data_id`),
  KEY `idx_data_sensor_time` (`sensor_id`, `recorded_at`),
  KEY `idx_data_time`        (`recorded_at`),
  CONSTRAINT `fk_data_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `Sensor`(`sensor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================================
--  DỮ LIỆU KHỞI TẠO
-- =====================================================================

-- Tài khoản mặc định: hiep / 123456   (hash bcrypt cost 12)
INSERT INTO `User` (`username`, `password`, `full_name`, `student_id`, `class`) VALUES
  ('hiep', '$2b$12$JtUc7pbn3qTn1/a9bYWkYuIWUH.dTifKFjWou1CGmMruaYhoJHoae',
   'Đàm Lê Đức Hiệp', 'B23DCAT096', 'D23CQAT01-B');

-- device_id phải khớp với firmware ESP32: 1 -> LED_PIN (GPIO2), 2 -> LED2_PIN (GPIO22)
INSERT INTO `Device` (`device_id`, `device_name`, `device_type`, `is_active`) VALUES
  (1, 'Đèn',  'LED', FALSE),
  (2, 'Quạt', 'Fan', FALSE);

-- sensor_id 1/2/3 tương ứng 3 trường temp/humid/light trong payload topic Data_Sensor
INSERT INTO `Sensor` (`sensor_id`, `sensor_name`, `sensor_type`) VALUES
  (1, 'DHT11', 'Nhiệt độ'),
  (2, 'DHT11', 'Độ ẩm'),
  (3, 'LDR',   'Ánh sáng');
