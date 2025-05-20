# data_process.py
from log_config import logger
from typing import Callable, List, Dict, Optional


class DataProcessor:
    """传感器数据处理核心类"""

    def __init__(self, config):
        """
        初始化数据处理实例
        :param config: 配置管理对象，需包含 rb87_ggr 等参数
        """
        self.config = config

    @staticmethod
    def _clean_value(value: str) -> str:
        """
        数据清洗辅助方法
        :param value: 原始字符串数据
        :return: 去除空字符和控制字符后的干净数据
        """
        return value.replace('\x00', '').strip()

    def parse_line(self, raw_line: str) -> Optional[Dict]:
        """
        解析单行传感器数据
        :param raw_line: 原始数据行
        :return: 结构化数据字典 或 None
        """
        try:
            parts = raw_line.split("\t")
            if len(parts) not in (4, 5):
                logger.exception(f"无效数据列数: {len(parts)}")
                raise ValueError(f"无效数据列数: {len(parts)}")

            # 清洗并转换数据字段
            cleaned = [self._clean_value(p) for p in parts]

            mag1_fre = float(cleaned[0])
            mag2_fre = float(cleaned[1])
            voltage1 = float(cleaned[2])
            voltage2 = float(cleaned[3])
            serial_number = int(cleaned[4]) if len(cleaned) == 5 else 0

            # 计算磁场值
            mag1 = mag1_fre / self.config.rb87_ggr
            mag2 = mag2_fre / self.config.rb87_ggr

            return {
                "Mag1": mag1,
                "Mag2": mag2,
                "Vol1": voltage1,
                "Vol2": voltage2,
                "SerialNumber": serial_number
            }
        except (ValueError, IndexError) as e:
            logger.error(f"数据解析失败: {e} 原始数据: {raw_line}")
            return None

    def aggregate_period_data(
            self,
            data_buffer: List[Dict],
            aggregation_func: Callable
    ) -> Optional[Dict]:
        """
        聚合处理周期数据
        :param data_buffer: 原始数据缓存列表
        :param aggregation_func: 聚合函数（max/min/mean等）
        :return: 聚合后的统计数据字典
        """
        if not data_buffer:
            logger.warning("空数据缓存无法聚合")
            return None

        try:
            aggregated = {}
            for key in ["Mag1", "Mag2", "Vol1", "Vol2"]:
                values = [entry[key] for entry in data_buffer]
                aggregated[key] = aggregation_func(values)

            aggregated["SerialNumber"] = data_buffer[-1]["SerialNumber"]
            return aggregated
        except KeyError as e:
            logger.error(f"数据字段缺失: {e}")
            return None
        except Exception as e:
            logger.exception(f"数据聚合异常: {e}")
            return None

