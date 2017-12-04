#!/usr/bin/env python
# -*- coding: utf-8 -*-

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import argparse
import glob
import gzip
import json
import logging
import re
import time
from string import Template

import configparser

config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "MONITOR_LOG": "monitor_log.log",
            "TS_FILE_PATH": "/var/tmp/log_analyzer.ts",
            "CONFIG_DEFAULT_PATH": '/usr/local/etc/log_analyzer.conf',
            "REQUEST_TIME_POS": -1,
            "URL_POS": 7
        }


def parse_config(conf, config_path):
    config_from_file = configparser.ConfigParser()
    config_from_file.read(config_path or conf['CONFIG_DEFAULT_PATH'])
    new_config = {}
    if 'CONFIG' in config_from_file:
        for option in config_from_file['CONFIG']:
            key = option.upper()
            value = config_from_file['CONFIG'][option]
            if key == 'REPORT_SIZE':
                value = int(value)
            new_config[key] = value
    conf.update(new_config)
    return conf


def set_timestamp(conf):
    with open(conf['TS_FILE_PATH'], 'a') as af:
        af.write(str(time.time()) + '\n')


def get_parsed_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="config file path", nargs=1)
    return parser.parse_args()


def get_log_date_name(log_file_path):
    ''' Отдаем дату из название файла '''
    filename = log_file_path.split('/')[-1]
    if filename.endswith(".gz"):
        filename = filename[:-3]
    return filename[-8:]


def is_log_parsed(log_date_name, conf):
    ''' Если существует report.html, совпадающий с датой в имени nginx-access-ui.log,
        то считаем, что лог уже парсился '''
    date_name = log_date_name
    list_of_files = glob.glob(conf["REPORT_DIR"]+'/*')
    for filename in list_of_files:
        if filename.find(date_name) != -1:
            return True
    return False


def find_last_log_file_path(conf):
    # паттерн для поиска ui nginx логов с датой из 8 символов в названии.
    pattern = re.compile(r'nginx-access-ui.log-(\d{8})\D*')

    list_of_files = glob.glob(conf["LOG_DIR"]+'/*')
    list_of_nginx_ui_log = []
    for filename in list_of_files:
        result = pattern.search(filename)
        if result:
            list_of_nginx_ui_log.append(filename)
    list_of_nginx_ui_log.sort()
    if list_of_nginx_ui_log:
        return list_of_nginx_ui_log[-1]
    else:
        return ''


def parse_log_line(line, conf):
    line_rows = line.split(' ')
    url = line_rows[conf['URL_POS']]
    request_time = float(line_rows[conf['REQUEST_TIME_POS']])
    return url, round(request_time, 3)


def parse_logfile(log_file_path, conf):
    log = {}
    if log_file_path.endswith(".gz"):
        log_file = gzip.open(log_file_path, 'rb')
    else:
        log_file = open(log_file_path)
    for line in log_file:
        url, request_time = parse_log_line(line, conf)
        if url in log:
            log[url].append(request_time)
        else:
            log[url] = [request_time]
    log_file.close()
    return log


def calculate_report(log, conf):
    logs_count = 0
    logs_time = 0
    report_data = []

    for url, time_list in log.items():
        count = len(time_list)
        time_sum = round(sum(time_list), 3)
        report_data.append(
            {
                'url': url,
                'count': count,
                'time_max': max(time_list),
                'time_sum': time_sum,
                'time_med': find_median(time_list)
            }
        )
        logs_count += count
        logs_time += time_sum

    for i, entry in enumerate(report_data):
        entry.update(
            {
                'time_avg': round(entry['time_sum'] / entry['count'], 4),
                'count_perc': round(float(entry['count']) / logs_count * 100, 4),
                'time_perc': round(entry['time_sum'] / logs_time * 100, 3)
            }
        )
        report_data[i] = entry

    report_data = sorted(report_data, key=lambda d: d['time_avg'], reverse=True)[:conf['REPORT_SIZE']]
    return report_data


def save_report(report_data, conf, log_date_name):
    table_json = json.dumps(report_data)
    report_file_path = "{0}/report-{1}.html".format(conf['REPORT_DIR'],
                                                    log_date_name)
    with open('report.html', 'r') as f:
        html = Template(f.read()).safe_substitute(table_json=table_json)
        with open(report_file_path, 'w') as wf:
            wf.write(html)


def find_median(lst):
    n = len(lst)
    if n % 2 == 1:
        return sorted(lst)[n // 2]
    else:
        return sum(sorted(lst)[n // 2 - 1:n // 2 + 1]) / 2.0


def main():
    global config
    args = get_parsed_args()
    conf = parse_config(config, args.config)
    logging.basicConfig(filename=conf['MONITOR_LOG'], level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s')

    logging.info('Start program with config ' + str(conf))
    log_file_path = find_last_log_file_path(conf)
    if not log_file_path:
        logging.exception('Log file not found in log directory')
        return 0
    log_date_name = get_log_date_name(log_file_path)
    if is_log_parsed(log_date_name, conf):
        logging.info(log_file_path + ' log was previously processed')
    else:
        log = parse_logfile(log_file_path, conf)
        report = calculate_report(log, conf)
        save_report(report, conf, log_date_name)
    set_timestamp(conf)
    logging.info('Program end')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(e, exc_info=True)
