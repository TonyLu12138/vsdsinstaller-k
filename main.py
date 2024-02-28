#! /usr/bin/env python3

import argparse
import sys
from base import Logger
from replacement_installation import ReplacementInstallation

# 更换内核
def replace_kernel(re_in):
    re_in.change_kernel()

# 检查内核版本
def check_kernel_version(re_in):
    re_in.check_kernel_version()

# 安装 VersaSDS DEB
def install_versds_deb(re_in):
    re_in.install_versasds_deb()

# 卸载 VersaSDS DEB
def ubinstall_versds_deb(re_in):
    re_in.uninstall_versasds_deb()

# 安装 thin_send_recv
def install_thin_send_recv(re_in):
    re_in.install_thin_send_recv()

# 显示 DRBD/LINSTOR 版本
def display_drbd_linstor_version(re_in):
    re_in.get_versions()

def display_version():
    print("version: v1.0.2")

def main():
    parser = argparse.ArgumentParser(description='vsdsinstaller-k')
    parser.add_argument('-r', '--replace', action='store_true',
                        help='Replacement of the kernel')
    parser.add_argument('-c', '--check', action='store_true',
                        help='Checking the kernel version')
    parser.add_argument('-i', '--install', action='store_true',
                        help='Install VersaSDS DEB')
    parser.add_argument('-u', '--uninstall', action='store_true',
                        help='Uninstall VersaSDS DEB')
    parser.add_argument('-t', '--thin', action='store_true',
                        help='Install thin_send_recv')
    parser.add_argument('-d', '--display', action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('-v', '--version', action='store_true',
                        help='show version information')
    args = parser.parse_args()
    
    if args.version:
        display_version()
        sys.exit()
        
    logger = Logger("vsdsinstaller-k")
    re_in = ReplacementInstallation(logger)
    
    if args.replace:
        replace_kernel(re_in)
    elif args.check:
        check_kernel_version(re_in)
    elif args.install:
        install_versds_deb(re_in)
    elif args.uninstall:
        ubinstall_versds_deb(re_in)
    elif args.thin:
        install_thin_send_recv(re_in)
    elif args.display:
        display_drbd_linstor_version(re_in)
    else:
        print(f"请输入对应参数")
if __name__ == '__main__':
    main()