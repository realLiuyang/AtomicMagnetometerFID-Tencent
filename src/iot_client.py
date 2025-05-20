# iot_client.py
import sys
import os
import time
from typing import Optional
from log_config import logger
from iot_device_python_master_sdk.explorer.explorer import QcloudExplorer



class IoTClientManager:
    _instance: Optional["IoTClientManager"] = None
    qcloud: Optional[QcloudExplorer] = None
    template_initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_manager, sys_vars):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.config_manager = config_manager
        self.sys_vars = sys_vars

        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # 初始化QcloudExplorer
        self._initialize_qcloud()

    def _initialize_qcloud(self):
        """初始化腾讯云物联网平台连接"""
        try:
            # 1. 创建QcloudExplorer实例
            self.qcloud = QcloudExplorer(
                device_file = os.path.join(self.current_dir, "../config/device_info.json"),  # 替换为实际设备信息路径
                tls=True
            )

            # 2. 配置日志
            logger_iot = self.qcloud.logInit(
                self.qcloud.LoggerLevel.DEBUG,
                os.path.join(self.current_dir, "../logs/log_iot"),
                1024 * 1024 * 10,
                5,
                enable=True
            )

            # 3. 注册MQTT回调
            self.qcloud.registerMqttCallback(
                self._on_connect,
                self._on_disconnect,
                self._on_message,
                self._on_publish,
                self._on_subscribe,
                self._on_unsubscribe
            )

            # 4. 连接物联网平台
            self.qcloud.connect()

            # 5. 等待连接建立
            self._wait_for_connection()

            # 6. 初始化数据模板
            self._initialize_template()

        except Exception as e:
            logger.error(f"腾讯云SDK初始化失败: {e}")
            raise

    def _wait_for_connection(self, timeout=100):
        """等待MQTT连接建立"""
        start_time = time.time()
        while not self.qcloud.isMqttConnected():
            if time.time() - start_time > timeout:
                raise TimeoutError("MQTT连接超时")
            time.sleep(1)

    def _initialize_template(self):
        """初始化数据模板"""
        if self.template_initialized:
            return

        # 1. 模板初始化
        rc, mid = self.qcloud.templateInit(
            self.config_manager.product_key,
            self.config_manager.device_name,
            self._on_template_property,  # 属性回调
            self._on_template_action,  # 动作回调
            self._on_template_event,  # 事件回调
            self._on_template_service  # 服务回调
        )

        if rc != 0:
            raise RuntimeError(f"模板初始化失败，错误码: {rc}")

        # 2. 加载模板配置
        self.qcloud.templateSetup(
            self.config_manager.product_key,
            self.config_manager.device_name,
            os.path.join(self.current_dir, "../config/template_config.json")
              # 替换为实际模板配置路径
        )

        self.template_initialized = True

    # --- 回调函数区域 ---
    def _on_connect(self, flags, rc, userdata):
        logger.debug(f"MQTT连接建立: flags={flags}, rc={rc}")

    def _on_disconnect(self, rc, userdata):
        logger.warning(f"MQTT连接断开: rc={rc}")

    def _on_message(self, topic, payload, qos, userdata):
        logger.debug(f"收到消息: topic={topic}, payload={payload}")

    def _on_publish(self, mid, userdata):
        logger.debug(f"消息发布完成: mid={mid}")

    def _on_subscribe(self, qos, mid, userdata):
        logger.debug(f"订阅成功: qos={qos}, mid={mid}")

    def _on_unsubscribe(self, mid, userdata):
        logger.debug(f"取消订阅: mid={mid}")

    def _on_template_property(self, topic, qos, payload, userdata):
        logger.debug("%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
        if payload['method'] == 'control':
            """处理属性变更"""
            logger.info(f"收到属性变更: {payload}")
            try:
                params = payload.get('params', {})  # 提取params字段
                # 处理属性更新
                for key, value in params.items():
                    if self.sys_vars.is_variable_present(key):
                        self.sys_vars.set_variable_value(key, value)

                # 发送确认响应
                product_id = self.qcloud.getProductID()
                device_name = self.qcloud.getDeviceName()
                reply_param = self.qcloud.ReplyPara()
                reply_param.timeout_ms = 5 * 1000
                reply_param.status_msg = '\0'

                self.qcloud.templateControlReply(
                    product_id,
                    device_name,
                    reply_param
                )

            except Exception as e:
                logger.error(f"处理属性变更失败: {e}")

    def _on_template_action(self, topic, qos, payload, userdata):
        """处理动作调用"""
        logger.info(f"收到动作调用: {payload}")
        # 实现动作处理逻辑...

    def _on_template_event(topic, qos, payload, userdata):
        logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    def _on_template_service(topic, qos, payload, userdata):
        logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    # --- 业务方法更新 ---
    def publish_post_message(self, params):
        """上报设备属性"""
        try:
            # 1. 获取属性列表
            prop_list = self.qcloud.getPropertyList(
                self.config_manager.product_key,
                self.config_manager.device_name
            )

            # 2. 构建上报数据
            reports = self._construct_report(prop_list, params)
            params_in = self.qcloud.templateJsonConstructReportArray(
                self.config_manager.product_key,
                self.config_manager.device_name,
                reports
            )

            # 3. 上报属性
            rc, mid = self.qcloud.templateReport(
                self.config_manager.product_key,
                self.config_manager.device_name,
                params_in
            )
            logger.debug(f'属性上报：{params_in}')
            if rc != 0:
                logger.error(f"属性上报失败，错误码: {rc}")

        except Exception as e:
            logger.error(f"属性上报异常: {e}")

    def _construct_report(self, prop_list, values):
        """构建符合模板要求的数据结构"""
        report = {}
        for prop in prop_list:
            if prop.key in values:
                report[prop.key] = {
                    "value": values[prop.key],
                    "time": int(time.time() * 1000)
                }
        return {"reported": report}

    def get_client(self):
        """获取底层MQTT客户端（如仍需访问）"""
        return self.qcloud

    def getProductID(self):
        return self.qcloud.getProductID()

    def getDeviceName(self):
        return self.qcloud.getDeviceName()

    def construct_report(self, product_id, device_name, data):
        return self.qcloud.templateJsonConstructReportArray(product_id, device_name, data)

    def template_report(self,product_id, device_name, payload):
        return self.qcloud.templateReport(product_id, device_name, payload)