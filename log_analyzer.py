#!/usr/bin/env python
# -*- coding: utf-8 -*-

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


import gzip
import glob
import os
import json
from datetime import datetime
import time
import configparser
import sys
import logging

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "MONITOR_LOG": "monitor_log.log",
    "TS_FILE_PATH": "/var/tmp/log_analyzer.ts"
}

CONFIG_DEFAULT_PATH = '/usr/local/etc/log_analyzer.conf'
OPEN_LOGS_PATH = 'open_log_names'
REQUEST_TIME_POS = -1
URL_POS = 7


def is_file_run(filename):
    try:
        with open(OPEN_LOGS_PATH, 'r') as f:
            for line in f:
                if filename in line:
                    return True
    except IOError:
        logging.exception("create file for open log filenames")
    with open(OPEN_LOGS_PATH, 'a') as af:
        af.write(filename + '\n')


def set_timestamp():
    with open(config['TS_FILE_PATH'], 'a') as af:
        af.write(str(time.time()) + '\n')


def set_config(config_path):
    config_from_file = configparser.ConfigParser()
    config_from_file.read(config_path or CONFIG_DEFAULT_PATH)
    new_configs = {}
    if 'CONFIG' in config_from_file:
        for option in config_from_file['CONFIG']:
            key = option.encode('ascii', 'ignore').upper()
            value = config_from_file['CONFIG'][option].encode('ascii', 'ignore')
            if key == 'REPORT_SIZE':
                value = int(value)
            new_configs[key] = value
    config.update(new_configs)

    if config.get('MONITOR_LOG', False):
        logging.basicConfig(filename=config['MONITOR_LOG'], level=logging.DEBUG,
                            format='[%(asctime)s] %(levelname).1s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='[%(asctime)s] %(levelname).1s %(message)s')


def get_last_log_file():
    list_of_files = glob.glob(config["LOG_DIR"]+'/*')
    last_file = max(list_of_files, key=os.path.getctime)
    return last_file


def parse_log_line(line):
    line_rows = line.split(' ')
    url = line_rows[URL_POS]
    request_time = float(line_rows[REQUEST_TIME_POS])
    return url, round(request_time, 3)


def get_log_from_logfile(filename):
    log_dict = {}
    if filename.endswith(".gz"):
        log = gzip.open(filename, 'rb')
    else:
        log = open(filename)
    for line in log:
        url, request_time = parse_log_line(line)
        if url in log_dict:
            log_dict[url].append(request_time)
        else:
            log_dict[url] = [request_time]
    log.close()
    return log_dict


def get_calculated_report(log_dict):
    return [
        {
            'url': url,
            'count': len(time_list),
            'time_max': max(time_list),
            'time_sum': round(sum(time_list), 3),
            'time_med': min(time_list)
        } for url, time_list in log_dict.items()
    ]


def get_updated_report(report_data):
    logs_count = sum((d['count'] for d in report_data))
    logs_time = sum((d['time_sum'] for d in report_data))
    for i, log in enumerate(report_data):
            log.update(
                {
                    'time_avg': round(log['time_sum'] / log['count'], 3),
                    'count_perc': round(log['count'] / logs_count * 100, 8),
                    'time_perc': round(log['time_sum'] / logs_time * 100, 3)
                })
            report_data[i] = log
    return report_data


def save_report(report_data):
    table_json = json.dumps(report_data)
    report_file_path = "{0}/report-{1}.html".format(config['REPORT_DIR'], datetime.now())
    with open('report.html', 'r') as f:
        with open(report_file_path, 'w') as wf:
            for line in f:
                if line.find('$table_json') != -1:
                    line = line.replace('$table_json', table_json)
                wf.write(line)


def split_to_args_and_kwargs(argv):
    kwargs = {}
    for i, arg in enumerate(argv):
        if arg.startswith('--'):
            kwargs[argv.pop(i).replace('--', '')] = argv.pop(i+1)
    return argv, kwargs


def main(argv):
    args, kwargs = split_to_args_and_kwargs(argv)
    set_config(kwargs.get('config', False))
    logging.info('Start program with config ' + str(config))
    filename = get_last_log_file()
    if is_file_run(filename):
        logging.info(filename + ' log was previously processed')
        logging.info('Program end')
        return True
    parsed_log = get_log_from_logfile(filename)
    report_data = get_calculated_report(parsed_log)
    report_data = get_updated_report(report_data)
    report_data = sorted(report_data, key=lambda d: d['time_avg'], reverse=True)
    save_report(report_data)
    set_timestamp()
    logging.info('Program end')


if __name__ == "__main__":
    main(sys.argv)
