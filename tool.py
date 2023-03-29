# -*- coding:utf-8 -*-
import os
import time
import pytz
import logging
from datetime import datetime

class TimeProcessTool:
    @staticmethod
    def convert_to_local_timestamp(utc_time_str, utc_format='%Y-%m-%dT%H:%M:%S',default_timezone='Asia/Shanghai'):
        utc_timezone = pytz.timezone('UTC')
        local_timezone = pytz.timezone('Asia/Shanghai')

        # 将UTC时间字符串a按照指定格式转换为datetime类型的对象
        utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
        # 将UTC时间转换为本地时间
        local_time = utc_timezone.localize(utc_time).astimezone(local_timezone)

        # 将本地时间转换为时间戳格式
        timestamp = local_time.timestamp()
        return timestamp

class LoggerTool:


    @staticmethod
    def get_rotating_log_handler(log_file_path):
        os_sep = os.sep
        format = '%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(levelname)s %(message)s'

        formatter = logging.Formatter(format)
        l_index = log_file_path.rfind(os_sep)
        directory_path = log_file_path[:l_index]
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        # 创建TimedRotatingFileHandler对象
        from logging.handlers import TimedRotatingFileHandler
        log_file_handler = TimedRotatingFileHandler(filename=log_file_path, when='D', interval=1, backupCount=100)
        log_file_handler.setFormatter(formatter)
        return log_file_handler
