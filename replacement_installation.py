#! /usr/bin/env python3
import os
import re
import sys
from prettytable import PrettyTable
from base import Base

current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

class ReplacementInstallation:
    def __init__(self, logger):
        self.base = Base(logger)
        self.logger = logger
        self.config = self.install_from_yaml()
    
    def install_from_yaml(self):
        yaml_filename = "config.yaml"
        
        yaml_path = os.path.join(current_dir, yaml_filename)
        # print(f"yaml的路径：{yaml_path}")
        try:
            if not os.path.isfile(yaml_path):
                raise FileNotFoundError(f"未找到 {yaml_filename} 文件\n请检查配置文件是否在当前路径或者配置文件名称是否为config.yaml")
            self.config = self.base.get_version_from_yaml("config", yaml_path)
            return self.config
        except FileNotFoundError as e:
            print(e)  
            sys.exit()

    def change_kernel(self):
        expected_architecture = self.config.get('architecture').strip() # 预期架构
        expected_kernel_version = self.config.get('kernel').strip() # 预期内核版本

        # 检查当前系统处理器架构和内核版本
        current_architecture = self.base.com("uname -p").stdout.strip()
        current_kernel_version = self.base.com("uname -r").stdout.strip()
        # 检查当前系统是否符合预期架构
        if current_architecture != expected_architecture:
            print(f"当前系统架构为：{current_architecture}，不符合预期，请检查。")
            self.logger.log(f"处理器架构不匹配。当前架构：{current_architecture}")
            return
        else:
            print(f"当前系统架构为：{current_architecture}，符合预期架构。")
                  
        # 检查当前内核版本是否符合预期版本
        if current_kernel_version not in expected_kernel_version: # 不符合 继续后续步骤
            print(f"当前内核版本为：{current_kernel_version}，不符合预期版本，准备更新内核")
            kernel_package_name = self.config.get('kernel-package').strip()
            tar_path = os.path.join(current_dir, kernel_package_name)
            # 检查内核安装包是否存在于当前路径
            try:
                if not os.path.exists(tar_path):
                    raise FileNotFoundError(f"在当前路径下找不到 {kernel_package_name} 包")
            except FileNotFoundError as e:
                print(e)
                sys.exit() 
            # 解压内核安装包
            command = f"tar -xzvf {kernel_package_name}"
            print("解压内核安装包中")
            result = self.base.com(command)
            self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
            exitcode = result.returncode
            if 0 != exitcode:
                print("解压失败，中止程序。")
                sys.exit()
            else:
                tar_path = os.path.join(current_dir, "kernel")
                print({tar_path})
                # 拷贝内核文件及内核模块
                command_a = f"cp {tar_path}/boot/* /boot/"
                result = self.base.com(command_a)
                self.logger.log(f"执行指令：{command_a}. \n执行结果：{result.stdout}")
                command_b = f"cp -r {tar_path}/lib/modules/5.4.0-131-generic /lib/modules/"
                result = self.base.com(command_b)
                self.logger.log(f"执行指令：{command_b}. \n执行结果：{result.stdout}")
                
                # 生成 initramfs 映像
                command_create = f"update-initramfs -c -k {expected_kernel_version}"
                result = self.base.com(command_create)
                self.logger.log(f"执行指令：{command_create}. \n执行结果：{result.stdout}")
               
                command_ls = f"ls /boot | grep initrd.img-{expected_kernel_version}"
                result = self.base.com(command_ls)
                self.logger.log(f"执行指令：{command_ls}. \n执行结果：{result.stdout}")
                if result.stdout.strip(): 
                    print("检查 initrd.img 文件存在")
                else:
                    print("检查 initrd.img 文件不存在。重新尝试生成 initramfs 映像")
                    result = self.base.com(command_create)
                    self.logger.log(f"再次执行指令：{command_create}. \n执行结果：{result.stdout}")
                    result = self.base.com(command_ls)
                    self.logger.log(f"再次执行指令：{command_ls}. \n执行结果：{result.stdout}")
                    if result.stdout.strip(): 
                        print("检查 initrd.img 文件存在")
                    else:
                        print("检查 initrd.img 文件不存在，程序终止")
                        sys.exit()
                        
                # 更新 grub
                command = f"sudo update-grub"
                result = self.base.com(command)
                self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
                if "done" not in result.stdout: 
                    print("更新 grub 失败，程序终止")
                    sys.exit()
                else:
                    print("更新 grub 成功")
        else:
            print(f"当前内核版本为：{current_kernel_version}，已是预期内核版本")

    def check_kernel_version(self):
        expected_kernel_version = self.config.get('kernel').strip() # 预期内核版本
        # 检查当前系统处理器架构和内核版本
        current_kernel_version = self.base.com("uname -r").stdout.strip()
        self.logger.log(f"执行指令：'uname -r'. \n执行结果：{current_kernel_version}")
        # 检查当前内核版本是否符合预期版本
        print(f"当前内核版本: {current_kernel_version}")
        if current_kernel_version not in expected_kernel_version:
            print("不符合预期内核版本")
        else:
            print("已是预期内核版本")

    def install_versasds_deb(self):
        VersaSDS_DEB = self.config.get('VersaSDS-DEB').strip() # 预期内核版本
        
        # 检查 DEB 包是否存在于当前路
        deb_package_path = os.path.join(current_dir, VersaSDS_DEB)
        try:
            if not os.path.exists(deb_package_path):
                raise FileNotFoundError(f"在当前路径下找不到 {VersaSDS_DEB} 包\n请检查安装包是否在当前路径或者安装包名称是否与配置文件一致。")
        except FileNotFoundError as e:
            print(e)
            sys.exit()

        self.base.com("apt update")

        # 安装依赖包和 Java
        command = "apt install -y flex xmlto po4a xsltproc asciidoctor python3-setuptools help2man unzip default-jre openjdk-11-jre-headless"
        print("开始安装依赖包和 Java，网络原因可能会花费较多时间")
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
        exit_code = result.returncode
        if exit_code == 0:
            print("apt install 命令成功执行")
        else:
            print("apt install 命令执行失败")
            print(f"错误信息：\n{result}")
            sys.exit()

        # 安装 VersaSDS (DRBD/LINSTOR)
        command = f"dpkg -i {VersaSDS_DEB}"
        print("开始安装VersaSDS")
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")

        # 检查安装
        command = f"dpkg -l | grep ^ii | grep versasds"
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
        if not result.stdout.strip(): 
            print("versasds 安装失败！")
            sys.exit()
        
        command = f"linstor --version"
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
        if "not" in result.stdout: 
            print("linstor 安装失败！")
            sys.exit()

        command = f"drbdadm --version"
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
        if "DRBD_KERNEL_VERSION=9" and "DRBDADM_VERSION=9" not in result.stdout:
            print("drbdadm 安装失败！")
            sys.exit()

        print("安装完成")
        
    def uninstall_versasds_deb(self):
        command = f"dpkg -r versasds"
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
        
        command = f"dpkg -P versasds"
        result = self.base.com(command)
        self.logger.log(f"执行指令：{command}. \n执行结果：{result.stdout}")
        
        command = f"dpkg -l | grep ^ii | grep versasds"
        result = self.base.com(command)
        if not result.stdout:
            print("卸载成功")
        else:
            print("卸载失败")
            self.logger.log(f"执行指令：{command}. 卸载失败\n执行结果：{result.stdout}")
        
    def get_versions(self):
        components = ["DRBD_KERNEL_VERSION", "DRBDADM_VERSION", "LINSTOR"]
        component_names = {
            "DRBD_KERNEL_VERSION": "DRBD",
            "DRBDADM_VERSION": "DRBDADM",
            "LINSTOR": "LINSTOR Client"
        }
        versions = {}

        try:
            drbdadm_output = self.base.com("drbdadm --version").stdout.strip()
            self.logger.log(f"执行指令：'drbdadm --version'. \n执行结果：{drbdadm_output}")
            linstor_output = self.base.com("linstor --version").stdout.strip()
            self.logger.log(f"执行指令：'linstor --version'. \n执行结果：{linstor_output}")
        except Exception as e:
            print(f"Error executing command: {e}")
            return

        for component in components:
            if component.startswith("DRBD"):
                pattern = re.compile(fr"{component}=(\S+)")
                match = re.search(pattern, drbdadm_output)
                if match:
                    versions[component_names[component]] = match.group(1)
            elif component == "LINSTOR":
                linstor_version = linstor_output.split("\n")[0].split(";")[0].split(" ")[-1]
                versions[component_names[component]] = linstor_version

        table = PrettyTable()
        table.field_names = ["组件", "版本"]
        column = ["DRBD", "DRBDADM", "LINSTOR Clent"]
        for component, version in versions.items():
            table.add_row([component, version])

        print(table)
        self.logger.log(f"显示版本：\n{table}")




