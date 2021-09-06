#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os, sys, shutil
import subprocess
from multiprocessing import cpu_count
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


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

    jam_command = f'perl {os.getcwd()}/jam.pl'

    # appending threads to jam command
    if threads > 0:
        jam_command += f' -j {threads}'
        print(f'\n---------线程数为：{threads}---------')
    else:
        print(f'\n---------默认线程数量---------')
    jam_command += f' {plat_preffix}Editor'
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

    profile_json = os.path.abspath(f'./artifacts/profile.json')
    shutil.copy(profile_json, os.path.abspath(f'{dest_folder}/profile.json'))


def loop_build(df: bool):
    print(f'默认 {df}')
    # Generate folder according to date and time
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = os.path.abspath(f'../reports{now}')

    # Create output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # loop cpu count, look up build time
    cores = cpu_count()
    if df:
        cores = 0
    for i in range(cores+1):
        if i != 1 and i % 2 != 0:
            continue
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
    for i, f in enumerate(folder_list):
        if os.path.isfile(f'{reports_folder}/{f}'):
            continue
        time_report_file = os.path.abspath(f'{reports_folder}/{f}/time_report.txt')
        if not os.path.exists(time_report_file):
            continue
        for key in data_res:
            data_res[key].append(0)
        lenth = len(data_res['cores'])
        f_title = f.split('_')
        j_idx = f_title[1].find('j')
        cores = f_title[1][j_idx+1:]
        data_res['cores'][lenth-1]=cores
        fp = open(time_report_file)
        lines = fp.readlines()
        for line in lines:
            if 'Total wall time' in line or 'items' in line:
                name, time = get_type_time(line)
                if name in data_res:
                    data_res[name][lenth-1] = time
                else:
                    data_res[name] = [0]*(lenth)
                    data_res[name][lenth-1] = time
        fp.close()
    res_df = pd.DataFrame(data_res)
    res_df.to_csv(data_res_csv, index=None)
    print(f'\n本次数据:{data_res_csv}')

def draw(reports_folder: str):
    # bar chart
    df = pd.read_csv(f'{reports_folder}/data_res.csv')
    x = df['cores']
    y = df['Total wall time']
    title = 'Total time'
    plt.figure(figsize=(10, 10), dpi=100)
    plt.title(title, fontdict={'fontsize': 20})
    plt.xlabel('cores', fontsize=20)
    plt.ylabel('Total wall time(sec)', fontsize=20)
    plt.bar(x, y)
    plt.savefig(f'./{title}.png')
    plt.show()

    # pie chart
    labels = df.columns[2:]
    for idx, row in df.iterrows():
        title = f'cores-{int(row[0:1])}'
        values = row[2:]
        plt.figure(figsize=(40, 20), dpi=100)
        plt.pie(values, labels=labels, autopct='%1.1f%%',
                shadow=False, startangle=180, labeldistance=1.1,
                wedgeprops={'edgecolor': 'w', 'linewidth': 5}, normalize=True,
                textprops={'fontsize': 20})

        plt.axis('equal')
        plt.title(title, fontdict={'fontsize': 20})
        plt.legend(fontsize=20, loc="best")
        plt.savefig(f'./{title}.png')
        plt.show()

# Entry point of this script
if __name__ == '__main__':
    default = False
    if len(sys.argv) > 1 and sys.argv[1] == 'default':
        default = True
    reports_folder = loop_build(default)
    collect_data(reports_folder)
    draw(reports_folder)
