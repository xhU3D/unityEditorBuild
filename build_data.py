#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os, sys, shutil
import subprocess
from multiprocessing import cpu_count
from datetime import datetime
import pandas as pd


# Get platform preffix according to host machine
def get_platform_preffix():
    plat = sys.platform
    if plat.startswith('linux'):
        return 'Linux'
    elif plat.startswith('win') or plat.startswith('cygwin'):
        return 'Win'
    elif plat.startswith('darwin'):
        return 'Mac'


# remove build and artifacts
def clean_build_state():
    # # Old Methods
    # if os.path.exists("artifacts/TundraBuildState.state"):
    #     os.remove("artifacts/TundraBuildState.state")
    # if os.path.exists("artifacts/buildprogrambuildprogram/TundraBuildState.state"):
    #     os.remove("artifacts/buildprogrambuildprogram/TundraBuildState.state")
    # for dir in os.listdir('artifacts'):
    #     if not dir.__contains__('Stevedore'):
    #
    # for root, dirs, files in os.walk(f'{os.getcwd()}/artifacts'):
    #     for name in files:
    #         if not name.__contains__('Stevedore'):
    #             os.remove(os.path.join(root, name))

    # New Methods
    if os.path.exists("build"):
        shutil.rmtree('build')
    if os.path.exists("artifacts"):
        shutil.rmtree('artifacts')


# build editor once
def build_editor(threads: int = 0, output_folder: str = os.path.abspath("../reports/")):
    # clean everytime before building
    try:
        clean_build_state()
    except:
        clean_build_state()

    # generate basic jam command
    plat_preffix = get_platform_preffix()
    # generate build report folder
    build_report_folder = f'{output_folder}/{plat_preffix}Editor_j{threads}_report'
    # Create folder
    if not os.path.exists(build_report_folder):
        os.makedirs(build_report_folder)

    jam_command = f'perl {os.getcwd()}/jam.pl {plat_preffix}Editor'

    # appending threads to jam command
    if threads > 0:
        jam_command += f' -j {threads}'
        print(f'\n---------线程数为：{threads}---------')
    else:
        print(f'\n---------默认线程数量---------')

    # redirect output
    jam_command += f' > {build_report_folder}/jam_{plat_preffix}Editor_j{threads}_log.txt'

    # fix for linux build
    if plat_preffix == 'Linux':
        jam_command = f'/bin/bash -c \'cd {os.getcwd()} && {jam_command}\''

    # build in subprocess
    print(f'\n 命令 {jam_command}')
    status, output = subprocess.getstatusoutput(jam_command)

    # return result
    print(output)
    return status, build_report_folder


# get time report
def get_time_report(report_path: str):
    jam_command = f'perl {os.getcwd()}/jam.pl time-report > {report_path}'
    # fix for linux
    if get_platform_preffix() == 'Linux':
        jam_command = f'/bin/bash -c \'cd {os.getcwd()} && {jam_command}\''

    # build in subprocess
    print(f'\n 命令 {jam_command}')
    status, output = subprocess.getstatusoutput(jam_command)

    # return result
    print(output)
    return status


def copy_build_profiles(build_report_folder: str):
    build_profile_dir = os.path.abspath(f'./artifacts/BuildProfile')
    dest_folder = os.path.abspath(f'{build_report_folder}/BuildProfile')

    # Create folder
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    files = os.listdir(build_profile_dir)
    for i in files:
        file_dir = os.path.abspath(f'{build_profile_dir}/{i}')
        dest_file_dir = os.path.abspath(f'{dest_folder}/{i}')
        shutil.copy(file_dir, dest_file_dir)


def loop_build(once: bool):
    print(f'默认 {once}')
    # Generate folder according to date and time
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = os.path.abspath(f'../reports{now}')

    # Create output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # loop cpu count, look up build time
    cores = cpu_count()
    if once:
        cores = 0
    for i in range(cores+1):
    # for i in range(1):
        # build editor
        build_status, build_report_folder = build_editor(threads=i, output_folder=output_folder)
        if build_status != 0:
            print('\n构建失败')
            continue

        # export time-report
        report_status = get_time_report(f'{build_report_folder}/time_report.txt')
        if report_status != 0:
            print('\ntime report 输出失败')

        # copy build report
        copy_build_profiles(build_report_folder)

    return output_folder


def get_type_time(line: str):
    strs = line.split(':')
    name = strs[0]
    time = strs[1].strip().split(' ')[0]
    time = round(float(time), 3)
    return name, time


def collect_data(reports_folder: str):
    data_res = {'cores': []}
    data_res_csv = os.path.abspath(f'{reports_folder}/data_res.csv')
    folder_list = os.listdir(reports_folder)
    for f in folder_list:
        if os.path.isfile(f'{reports_folder}/{f}'):
            continue
        f_title = f.split('_')
        j_idx = f_title[1].find('j')
        cores = f_title[1][j_idx+1:]
        data_res['cores'].append(int(cores))
        time_report_file = os.path.abspath(f'{reports_folder}/{f}/time_report.txt')
        fp = open(time_report_file)
        lines = fp.readlines()
        for line in lines:
            if 'Total wall time' in line or 'items' in line:
                name, time = get_type_time(line)
                if name in data_res:
                    data_res[name].append(time)
                else:
                    data_res[name] = [time]
        fp.close()
    res_df = pd.DataFrame(data_res)
    res_df.to_csv(data_res_csv, index=None)
    print(f'\n本次数据:{data_res_csv}')
    # data_res = pd.read_csv(data_res_csv)
    # data_res = pd.DataFrame(data_res)
    # plt.title("cores-totalTime")
    # plt.xlabel("cores")
    # plt.ylabel("totalTime(sec)")
    # x = data_res['cores']
    # y = data_res['Total wall time']
    # plt.bar(x,y,align='center')
    # plt.show()

# Entry point of this script
if __name__ == '__main__':
    once = False
    if len(sys.argv) > 1:
        once = True
    reports_folder = loop_build(once)
    # reports_folder = os.path.abspath(f'../reports2021-09-03_12-08-25')
    collect_data(reports_folder)
