# main.py
import time
from data_log import get_data_log_file
from init import sys_variables, device, serial_reader, data_processor, raspi, payload_builder
from log_config import logger


def main():
    """主函数"""
    logger.info("进入主函数...")

    # 获取数据日志文件路径
    data_log_file_path = get_data_log_file()

    product_id = device.getProductID()
    # logger.debug(f"已经获取product_id：{product_id}")
    device_name = device.getDeviceName()
    # logger.debug(f"已经获取device_name：{device_name}")

    with open(data_log_file_path, "a", encoding="utf-8") as data_log_file:
        logger.info(f"已经获取打开数据日志")

        try:
            start_time = time.time()
            data_buffer = []

            while True:
                switch_status = sys_variables.get_converted_value("SwitchUpload")

                logger.debug(f"上传开关状态为：{switch_status}")

                if switch_status:
                    # logger.debug("上传开关已经打开")
                    try:
                        line = serial_reader.read_data()
                    except Exception as e:
                        logger.error(f"串口读取失败: {e}")
                        continue  # 继续下一次循环

                    if line:
                        logger.debug(f"接收到数据: {repr(line)}")

                        # 记录到日志文件
                        data_log_file.write(line + "\n")
                        data_log_file.flush()

                        # 解析数据
                        parsed_data = data_processor.parse_line(line)
                        if parsed_data:
                            logger.debug(f"处理后的数据: {parsed_data}")
                            data_buffer.append(parsed_data)
                    else:
                        logger.debug(f"未收到有效数据或串口未连接")
                    # 达到周期时间，处理数据
                    if (time.time() - start_time) * 1000 >= sys_variables.get_converted_value("WorkMode") and len(data_buffer) > 0:
                        payload = payload_builder.build(data_buffer)

                        if payload:
                            logger.info(f"发布数据: {payload}")
                            payload_construct = device.construct_report(product_id, device_name, payload)
                            device.template_report(product_id, device_name, payload_construct)

                            # 重置计时器 & 清空数据缓存
                            start_time = time.time()
                            data_buffer.clear()

                time.sleep(0.002)  # 适当延时，减少 CPU 负荷

        except KeyboardInterrupt:
            logger.info("系统关闭中...")
        except Exception as e:
            logger.exception(f"运行时错误: {e}")
        finally:
            try:
                if serial_reader.is_open:
                    serial_reader.close()
                    logger.info("串口已关闭")
            except Exception as e:
                logger.error(f"关闭串口时发生错误: {e}")

            logger.info(f"串口数据已保存至 {data_log_file_path}")
            logger.info("系统已安全退出")


if __name__ == "__main__":
    main()
