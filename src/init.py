# init.py
from config import ConfigManager, VariableManager
from iot_client import IoTClientManager
from log_config import logger
from raspi_info import RaspiInfo
from serial_reader import MagnetometerReader
from data_process import DataProcessor
from payload_package import PayloadBuilder

# 配置管理器实例化
config_manager = ConfigManager()

# 变量管理器实例化
sys_variables = VariableManager()

# 设备客户端管理器实例化
device = IoTClientManager(config_manager, sys_variables)

# 磁力计读取器实例化
serial_reader = MagnetometerReader(config_manager)

# 数据处理容器实例化
data_processor = DataProcessor(config_manager)

# 树莓派信息实例化
raspi = RaspiInfo()

# 树莓派信息实例化
payload_builder = PayloadBuilder(sys_variables, data_processor, raspi)

# 简单日志输出，确认系统已初始化
logger.info("系统初始化完成")
