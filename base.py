#! /usr/bin/env python3

import subprocess
import yaml

class Base:
    def __init__(self, logger):
        self.logger = logger

    def com(self, command):
        try:
            result = subprocess.run(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
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
        
    


