#serial_reader.py
import serial
import time
from log_config import logger


class MagnetometerReader:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # 固定设备名称（根据系统调整，如Windows用COM3）
        self.serial_port = self.config_manager.serial_port  # 固定设备名
        self.baud_rate = self.config_manager.baud_rate
        self.serial_connection = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5  # 最大重连尝试次数

        self.initialize_serial()

    def initialize_serial(self):
        """初始化串口连接，成功返回True"""
        try:
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=0.02
            )
            logger.info(f"串口 {self.serial_port} 已打开，波特率 {self.baud_rate}")
            self.reconnect_attempts = 0  # 重置计数器
            return True
        except serial.SerialException as e:
            logger.error(f"打开串口失败: {e}")
            self.serial_connection = None
            return False

    def reconnect(self):
        """执行重连操作，返回是否成功"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"已达最大重连次数 {self.max_reconnect_attempts}，停止尝试")
            return False

        self.close()
        logger.info(f"尝试重连({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})...")
        time.sleep(2)  # 重连间隔
        success = self.initialize_serial()
        self.reconnect_attempts += 0 if success else 1
        return success

    def read_data(self):
        """读取数据，失败时自动重连"""
        # 检查连接状态
        if not self.is_open() and not self.reconnect():
            return None

        try:
            line = ""
            while True:
                chunk = self.serial_connection.read(1).decode(errors="ignore")
                if not chunk:  # 超时无数据
                    break
                line += chunk
                if chunk == "\n":
                    break
            return line.strip().replace("\x00", "") if line else None
        except serial.SerialException as e:
            logger.error(f"读取失败: {e}，触发重连")
            self.reconnect()
            return None

    def close(self):
        """安全关闭串口"""
        if self.is_open():
            self.serial_connection.close()
            logger.info("串口已关闭")

    def is_open(self):
        return self.serial_connection.is_open if self.serial_connection else False