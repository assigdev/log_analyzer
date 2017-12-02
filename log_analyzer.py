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
import time
from string import Template

import configparser


class Configure(object):
    def __init__(self):
        self._config = {
            "REPORT_SIZE": 1000,
            "REPORT_DIR": "./reports",
            "LOG_DIR": "./log",
            "MONITOR_LOG": "monitor_log.log",
            "TS_FILE_PATH": "/var/tmp/log_analyzer.ts",
            "CONFIG_DEFAULT_PATH": '/usr/local/etc/log_analyzer.conf',
            "REQUEST_TIME_POS": -1,
            "URL_POS": 7
        }
        parser = argparse.ArgumentParser()
        parser.add_argument("-c", "--config", help="config file path", nargs=1)
        self._args = parser.parse_args()

        logging.basicConfig(filename=self.get_config('MONITOR_LOG'), level=logging.INFO,
                            format='[%(asctime)s] %(levelname).1s %(message)s')

    def parse_config(self):
        config_from_file = configparser.ConfigParser()
        config_from_file.read(self._args.config or self.get_config('CONFIG_DEFAULT_PATH'))
        new_config = {}
        if 'CONFIG' in config_from_file:
            for option in config_from_file['CONFIG']:
                key = option.upper()
                value = config_from_file['CONFIG'][option]
                if key == 'REPORT_SIZE':
                    value = int(value)
                new_config[key] = value
        self._config.update(new_config)

    def get_config(self, key):
        return self._config.get(key, False)

    def set_timestamp(self):
        with open(self.get_config('TS_FILE_PATH'), 'a') as af:
            af.write(str(time.time()) + '\n')

    def __str__(self):
        return str(self._config)


class LogParser(object):
    def __init__(self, conf):
        self.log_file_path = ''
        self.log = {}
        self.conf = conf

    def get_log_date_name(self):
        ''' Отдаем дату из название файла '''
        filename = self.log_file_path.split('/')[-1]
        if filename.endswith(".gz"):
            filename = filename[:-3]
        return filename[-8:]

    def is_log_parsed(self):
        ''' Если существует report.html, совпадающий с датой в имени nginx-access-ui.log,
            то считаем, что лог уже парсился '''
        date_name = self.get_log_date_name()
        list_of_files = glob.glob(self.conf.get_config("REPORT_DIR")+'/*')
        for filename in list_of_files:
            if filename.find(date_name) != -1:
                return True
        return False

    def find_last_log_file_path(self):
        list_of_files = glob.glob(self.conf.get_config("LOG_DIR")+'/*')
        list_of_nginx_ui_log = []
        for filename in list_of_files:
            if filename.find('nginx-access-ui.log'):
                list_of_nginx_ui_log.append(filename)
        list_of_nginx_ui_log.sort()

        self.log_file_path = list_of_nginx_ui_log[-1]

    def _parse_log_line(self, line):
        line_rows = line.split(' ')
        url = line_rows[self.conf.get_config('URL_POS')]
        request_time = float(line_rows[self.conf.get_config('REQUEST_TIME_POS')])
        return url, round(request_time, 3)

    def parse_logfile(self):
        if self.log_file_path.endswith(".gz"):
            log_file = gzip.open(self.log_file_path, 'rb')
        else:
            log_file = open(self.log_file_path)
        for line in log_file:
            url, request_time = self._parse_log_line(line)
            if url in self.log:
                self.log[url].append(request_time)
            else:
                self.log[url] = [request_time]
        log_file.close()

    def get_log(self):
        return self.log


class Report(object):

    def __init__(self, log, conf):
        self.log = log
        self.conf = conf
        self.report_data = []

    def calculate_report(self):
        self.report_data = [
            {
                'url': url,
                'count': len(time_list),
                'time_max': max(time_list),
                'time_sum': round(sum(time_list), 3),
                'time_med': self._find_median(time_list)
            } for url, time_list in self.log.get_log().items()
        ]

        logs_count = sum((d['count'] for d in self.report_data))
        logs_time = sum((d['time_sum'] for d in self.report_data))
        for i, entry in enumerate(self.report_data):
            entry.update(
                {
                    'time_avg': round(entry['time_sum'] / entry['count'], 4),
                    'count_perc': round(float(entry['count']) / logs_count * 100, 4),
                    'time_perc': round(entry['time_sum'] / logs_time * 100, 3)
                }
            )
            self.report_data[i] = entry
        self.report_data = sorted(self.report_data,
                                  key=lambda d: d['time_avg'],
                                  reverse=True
                                  )[:self.conf.get_config('REPORT_SIZE')]

    def save_report(self):
        table_json = json.dumps(self.report_data)
        report_file_path = "{0}/report-{1}.html".format(self.conf.get_config('REPORT_DIR'),
                                                        self.log.get_log_date_name())
        with open('report.html', 'r') as f:
            html = Template(f.read()).safe_substitute(table_json=table_json)
            with open(report_file_path, 'w') as wf:
                wf.write(html)

    def _find_median(self, lst):
        n = len(lst)
        if n % 2 == 1:
            return sorted(lst)[n // 2]
        else:
            return sum(sorted(lst)[n // 2 - 1:n // 2 + 1]) / 2.0

def main():
    conf = Configure()
    conf.parse_config()
    logging.info('Start program with config ' + str(conf))

    log = LogParser(conf)
    log.find_last_log_file_path()
    log.is_log_parsed()
    if log.is_log_parsed():
        logging.info(log.log_file_path + ' log was previously processed')
    else:
        log.parse_logfile()
        report = Report(log, conf)
        report.calculate_report()
        report.save_report()
    conf.set_timestamp()
    logging.info('Program end')


if __name__ == "__main__":
    main()
