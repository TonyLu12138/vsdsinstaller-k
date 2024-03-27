#! /usr/bin/env python3
import os
import re
import shutil
import sys
import tarfile
import time
from prettytable import PrettyTable
from base import Base

current_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

class ReplacementInstallation:
    def __init__(self, logger):
        self.base = Base()
        self.logger = logger
        self.config = None
    
    def install_from_yaml(self):
        yaml_filename = "vsdsinstaller-k_config.yaml"
        
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

    # 获取解压后的文件夹名字
    def get_extracted_folder(self, kernel_package_name):
        
        folder_name = None
        with tarfile.open(kernel_package_name, 'r') as tar:
            folder_name = os.path.commonprefix(tar.getnames())
        return folder_name
    
    # 检查 copymods
    def check_copymods(self):
        try:
            command = "mount | grep copymods"
            result = self.base.com(command)

            if result.stdout:
                print("系统存在 copymods RAMFS 挂载，请检查系统内核模块")
                sys.exit()
            else:
                print("系统中未发现 copymods RAMFS 挂载，可以继续进行后续步骤")
        except Exception as e:
            print(f"发生错误：{e}")

    def change_kernel(self):
        if not self.config:
            self.config = self.install_from_yaml()

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
            
            print("执行检查 copymods 方法")
            self.check_copymods()

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
            command = f"sudo tar -xzvf {kernel_package_name}"
            print("解压内核安装包中")
            result = self.base.com(command)
            exitcode = result.returncode
            if exitcode != 0:
                print("解压失败，中止程序。")
                sys.exit()
            else:
                extracted_folder = self.get_extracted_folder(tar_path)
                tar_path = os.path.join(current_dir, extracted_folder)  ###########
                # print(f"{tar_path}")
                
                # 拷贝内核文件及内核模块
                command_a = f"sudo cp {tar_path}/boot/* /boot/"
                result = self.base.com(command_a)
                self.logger.log(f"返回码：{result.returncode}")
                if result.returncode != 0:
                    print("替换内核失败，程序终止")
                    sys.exit()
                command_b = f"sudo cp -r {tar_path}/lib/modules/5.4.0-131-generic /lib/modules/"
                result = self.base.com(command_b)
                self.logger.log(f"返回码：{result.returncode}")
                if result.returncode != 0:
                    print("替换内核失败，程序终止")
                    sys.exit()

                time.sleep(5)

                # 生成 initramfs 映像
                print(f"更新 initramfs 中")
                command_create = f"sudo update-initramfs -c -k {expected_kernel_version}"
                result = self.base.com(command_create)
                print(f"执行生成 initramfs 映像. \n执行结果：{result.stdout}")
                if result.returncode == 0:
                    command_ls = f"ls /boot | grep initrd.img-{expected_kernel_version}"
                    result = self.base.com(command_ls)
                    # self.logger.log(f"执行指令：{command_ls}. \n执行结果：{result.stdout}")
                    if result.stdout.strip(): 
                        print("检查 initrd.img 文件存在")
                    else:
                        print("检查 initrd.img 文件不存在。重新尝试生成 initramfs 映像")
                        self.logger.log(f"检查 initrd.img 文件不存在。重新尝试生成 initramfs 映像")
                        result = self.base.com(command_create)
                        # self.logger.log(f"再次执行指令：{command_create}. \n执行结果：{result.stdout}")
                        result = self.base.com(command_ls)
                        # self.logger.log(f"再次执行指令：{command_ls}. \n执行结果：{result.stdout}")
                        if result.stdout.strip(): 
                            print("检查 initrd.img 文件存在")
                        else:
                            print("检查 initrd.img 文件不存在，程序终止")
                            sys.exit()
                else:
                    print("生成 initramfs 映像失败")  
                    self.logger.log(f"生成 initramfs 映像失败")    
                    sys.exit()  

                # 更新 grub
                command = f"sudo update-grub"
                result = self.base.com(command)
                if "done" not in result.stdout: 
                    print("更新 grub 失败，程序终止")
                    sys.exit()
                else:
                    print("更新 grub 成功")

            print(f"内核版本更新完成")
        else:
            print(f"当前内核版本为：{current_kernel_version}，已是预期内核版本")

    def check_kernel_version(self):
        if not self.config:
            self.config = self.install_from_yaml()

        expected_kernel_version = self.config.get('kernel').strip() # 预期内核版本
        # 检查当前系统处理器架构和内核版本
        current_kernel_version = self.base.com("uname -r").stdout.strip()
        # self.logger.log(f"执行指令：'uname -r'. \n执行结果：{current_kernel_version}")
        # 检查当前内核版本是否符合预期版本
        print(f"当前内核版本: {current_kernel_version}")
        if current_kernel_version not in expected_kernel_version:
            print("不符合预期内核版本")
        else:
            print("已是预期内核版本")

    def install_versasds_deb(self):
        if not self.config:
            self.config = self.install_from_yaml()

        VersaSDS_DEB = self.config.get('VersaSDS-DEB').strip() # 预期内核版本
        
        # 检查 DEB 包是否存在于当前路
        deb_package_path = os.path.join(current_dir, VersaSDS_DEB)
        try:
            if not os.path.exists(deb_package_path):
                raise FileNotFoundError(f"在当前路径下找不到 {VersaSDS_DEB} 包\n请检查安装包是否在当前路径或者安装包名称是否与配置文件一致。")
        except FileNotFoundError as e:
            print(e)
            sys.exit()

        print("执行 apt update, 请耐心等待")
        self.base.com("sudo apt update")

        # 安装依赖包和 Java
        command = "sudo apt install -y flex xmlto po4a zstd xsltproc asciidoctor python3-setuptools help2man unzip default-jre openjdk-11-jre-headless"
        print("开始安装依赖包和 Java，网络原因可能会花费较多时间")
        result = self.base.com(command)
        exit_code = result.returncode
        if exit_code == 0:
            print("apt install 命令成功执行")
        else:
            print("apt install 命令执行失败")
            print(f"错误信息：\n{result}")
            sys.exit()

        # 安装 VersaSDS (DRBD/LINSTOR)
        command = f"sudo dpkg -i {VersaSDS_DEB}"
        print("开始安装VersaSDS")
        result = self.base.com(command)
        
        # 检查安装
        command = f"dpkg -l | grep ^ii | grep versasds"
        result = self.base.com(command)
        if not result.stdout.strip(): 
            print("versasds 安装失败！")
            sys.exit()
        
        command = f"linstor --version"
        result = self.base.com(command)
        if "not" in result.stdout: 
            print("linstor 安装失败！")
            sys.exit()

        command = f"drbdadm --version"
        result = self.base.com(command)
        if "DRBD_KERNEL_VERSION=9" and "DRBDADM_VERSION=9" not in result.stdout:
            print("drbdadm 安装失败！")
            sys.exit()

        print("安装完成")

    def install_thin_send_recv(self):
        if not self.config:
            self.config = self.install_from_yaml()

        # 检查 thin_send_recv 二进制文件是否存在于当前路
        thin_send_recv_path = os.path.join(current_dir, "thin_send_recv")
        try:
            if not os.path.exists(thin_send_recv_path):
                raise FileNotFoundError(f"在当前路径下找不到 thin_send_recv 二进制文件\n请检查文件是否在当前路径。")
        except FileNotFoundError as e:
            print(e)
            sys.exit()

        # 检查 thin_send_recv 是否已经存在
        if os.path.exists("/usr/bin/thin_send_recv"):
            print("thin_send_recv 已经存在，跳过安装步骤")
            # 继续后续操作，例如权限修改和创建软链接
        else:
            # 复制 thin_send_recv 到 /usr/bin/
            shutil.copy(thin_send_recv_path, "/usr/bin/")

            # 修改权限
            chmod_command = "chmod 0755 /usr/bin/thin_send_recv"
            result = self.base.com(chmod_command)
            exit_code = result.returncode
            if exit_code == 0:
                pass
                # print("文件 thin_send_recv 权限修改成功")
            else:
                print("文件 thin_send_recv 权限修改失败")
                sys.exit()

            # 创建软链接 thin_send
            ln_send_command = "ln -s /usr/bin/thin_send_recv /usr/bin/thin_send"
            result = self.base.com(ln_send_command)

            # 创建软链接 thin_recv
            ln_recv_command = "ln -s /usr/bin/thin_send_recv /usr/bin/thin_recv"
            result = self.base.com(ln_recv_command)

            thin_send = self.base.com("thin_send -v").stdout
            thin_recv = self.base.com("thin_recv -v").stdout
            if "1.0.2" in thin_send and "1.0.2" in thin_recv:
                print("安装 thin_send_recv 成功")
            else:
                print("安装 thin_send_recv 失败")
                sys.exit()

    def uninstall_versasds_deb(self):
        command_check = f"dpkg -l | grep ^ii | grep versasds"
        result = self.base.com(command_check)
        if result.stdout.strip():
            self.base.com(f"dpkg -r versasds")
            self.base.com(f"dpkg -P versasds")
            result = self.base.com(command_check)
            if not result.stdout:
                print("卸载成功")
            else:
                print("卸载失败")
                self.logger.log(f"卸载失败")
        else:
            print("未安装 VersaSDS DEB，无需卸载")
            self.logger.log(f"未安装 VersaSDS DEB，无需卸载")

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
            # self.logger.log(f"执行指令：'drbdadm --version'. \n执行结果：{drbdadm_output}")
            linstor_output = self.base.com("linstor --version").stdout.strip()
            # self.logger.log(f"执行指令：'linstor --version'. \n执行结果：{linstor_output}")
        except Exception as e:
            print(f"Error executing command: {e}")
            return

        for component in components:
            if component.startswith("DRBD"):
                pattern = re.compile(fr"{component}=(\S+)")
                match = re.search(pattern, drbdadm_output)
                if match:
                    versions[component_names[component]] = match.group(1)
                else:
                    versions[component_names[component]] = "Not Found"  # 如果未找到版本信息，设为 "Not Found"
            elif component == "LINSTOR":
                if "not found" not in linstor_output:
                    linstor_version = linstor_output.split("\n")[0].split(";")[0].split(" ")[-1]
                    versions[component_names[component]] = linstor_version
                else:
                    versions[component_names[component]] = "Not Found"

        table = PrettyTable()
        table.field_names = ["组件", "版本"]
        column = ["DRBD", "DRBDADM", "LINSTOR Clent"]
        for component, version in versions.items():
            table.add_row([component, version])

        print(table)
        self.logger.log(f"显示版本：\n{table}")




