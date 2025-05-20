# payload_package.py
import time


class PayloadBuilder:
    """有效载荷构建器"""

    def __init__(self, sys_vars, data_proc, raspi_sys):
        """
        初始化构建器
        :param sys_vars: 系统变量管理对象
        :param data_proc: 数据处理对象
        :param raspi_sys: 系统信息对象
        """
        self.sys_vars = sys_vars
        self.data_proc = data_proc
        self.raspi_sys = raspi_sys

    def build(self, data_buffer):
        """
        构建完整数据载荷
        :param data_buffer: 原始数据缓冲区
        :param upload_switch: 上传开关状态
        :return: 结构化数据字典
        """
        # 基础系统信息
        base_info = {
            "timestamp": int(time.time()),
            "SwitchUpload": self.sys_vars.get_variable_value("SwitchUpload"),
            "WorkMode": self.sys_vars.get_variable_value("WorkMode"),
            "FilterType": self.sys_vars.get_variable_value("FilterType")
        }

        # 树莓派系统信息
        system_info = self.raspi_sys.get_system_info()

        # 处理传感器数据
        processed_data = self.data_proc.aggregate_period_data(
            data_buffer,
            self.sys_vars.get_converted_value("FilterType")
        )

        # 组合所有数据源
        return {**base_info, **system_info, **processed_data}