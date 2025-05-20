# config.py
import json
import os
import statistics

from log_config import logger


class ConfigManager:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.device_file_path = os.path.join(self.current_dir, "../config/device_info.json")
        self.serial_file_path = os.path.join(self.current_dir, "../config/serial_info.json")

        with open(self.device_file_path, 'r') as f:
            device_info = json.load(f)
            # 直接映射的字段
            self.product_key = device_info['productId']
            self.device_name = device_info['deviceName']
            # self.client_id = device_info['key_deviceinfo']['deviceSecret']

        with open(self.serial_file_path, 'r') as f:
            serial_info = json.load(f)
            self.serial_port = serial_info['serial_port']
            self.baud_rate = serial_info['baud_rate']

        self.rb87_ggr = 7.0

        self.filter_types = [0, 1, 2, 3]


class VariableManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize_variables()
        return cls._instance

    def initialize_variables(self):
        """初始化变量相关设置"""
        self.variables = {
            "SwitchUpload": 0,
            "WorkMode": 0,
            "FilterType": 0,  # 修正 typo
        }
        self.switch_table = [False, True]
        self.work_mode_table = [1000, 200]
        self.filter_type_functions = [
            statistics.mean,
            max,
            min,
            self.last
        ]

    def is_variable_present(self, name):
        """检查变量是否存在"""
        return name in self.variables

    def get_variable_value(self, name):
        """获取变量值"""
        if self.is_variable_present(name):
            return self.variables[name]
        logger.exception(f"变量 {name} 不存在")
        raise KeyError(f"变量 {name} 不存在")

    def set_variable_value(self, name, value):
        """设置变量值"""
        if self.is_variable_present(name):
            self.variables[name] = value
        else:
            logger.exception(f"变量 {name} 不存在")
            raise KeyError(f"变量 {name} 不存在")

    def get_converted_value(self, name):
        """获取变量的转换值"""
        if not self.is_variable_present(name):
            logger.exception(f"变量 {name} 不存在")
            raise KeyError(f"变量 {name} 不存在")

        value = self.variables[name]
        if name == "SwitchUpload":
            return self.switch_table[value]
        if name == "WorkMode":
            return self.work_mode_table[value]
        if name == "FilterType":
            return self.filter_type_functions[value]
        logger.exception(f"变量 {name} 不支持转换")
        raise ValueError(f"变量 {name} 不支持转换")

    @staticmethod
    def last(data):
        """返回列表中的最后一个值"""
        if not data:
            logger.exception("输入列表为空")
            raise ValueError("输入列表为空")
        return data[-1]
