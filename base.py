#! /usr/bin/env python3
import atexit
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import datetime
import subprocess
import yaml

class Base:
    def __init__(self):
        self.logger = Logger("vsdsinstaller-k")

    def com(self, command):
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
            self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.log(f"命令 {command} 执行失败 {e}")
            return f"命令执行失败: {str(e)}"

    def get_version_from_yaml(self, software, yaml_path):
        try:
            with open(yaml_path, 'r') as file:
                data = yaml.safe_load(file)
                return data.get(software, None)
        except Exception as e:
            self.logger.log(f"读取YAML文件失败: {e}")
            return None
        

# 获取当前脚本所在的目录
current_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
log_directory = os.path.join(current_directory, "logs")  # 日志文件夹路径

if not os.path.exists(log_directory):
    os.makedirs(log_directory)  # 如果文件夹不存在，创建它


class SingletonLogger(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Logger(metaclass=SingletonLogger):
    def __init__(self, task_name, debug_enabled=False):
        self.logger = logging.getLogger(f"Debug_{task_name}")
        self.logger.setLevel(logging.DEBUG)
        self.name = f"{task_name}_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        self.debug_log_file = os.path.join(log_directory, self.name)
        self.debug_enabled = debug_enabled  # Set initial debug state

        file_handler = TimedRotatingFileHandler(
            self.debug_log_file, when='midnight', interval=1, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        atexit.register(self.close_logger)  # 注册关闭日志的方法到 atexit 模块

    def log(self, message):
        self.logger.debug(message)

    def space(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.write('\n')

    def close_logger(self):
        handlers = self.logger.handlers[:]
        for handler in handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.write('\n' + '-' * 50 + ' End of Log ' + '-' * 50 + '\n')
                handler.flush()
                handler.close()
                self.logger.removeHandler(handler)



