import unittest
import os
import errno
import shutil
from tests_fixtures.data import LOG_DATA, LOG_FILE_DATA
from log_analyzer import Configure, LogParser, Report


class ConfigureTestCase(unittest.TestCase):
    def setUp(self):
        self.conf = Configure()

    def test_default_config(self):
        self.assertEqual(self.conf.get_config('REPORT_SIZE'), 1000)
        self.assertEqual(self.conf.get_config('REPORT_DIR'), './reports')
        self.assertEqual(self.conf.get_config('LOG_DIR'), './log')


class LogParserTestCase(unittest.TestCase):
    def setUp(self):
        self.log_parse = LogParser(Configure())

        # for find_last_log_file_path
        path = 'test_log'
        self.log_parse.conf._config['LOG_DIR'] = path
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.first_file = path+"/nginx-access-ui.log-20170630"
        self.second_file = path+"/nginx-access-ui.log-20170631"
        f1 = open(self.first_file, 'a')
        f1.close()
        f2 = open(self.second_file, 'a')
        f2.write(LOG_FILE_DATA)
        f2.close()

        # for parse_log_line
        self.line_1 = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
        self.line_1_result = '/api/v2/banner/25019354', 0.390
        self.line_2 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199'
        self.line_2_result = '/api/v2/banner/16852664', 0.199
        self.line_3 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/1717161 HTTP/1.1" 200 2116 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752771" "712e90144abee9" 0.138'
        self.line_3_result = '/api/v2/banner/1717161', 0.138
        self.line_3_bad_result = '/api/v2/banner/1717161', 0.136

    def tearDown(self):
        shutil.rmtree(self.log_parse.conf._config['LOG_DIR'])

    def test_find_last_log_file_path(self):
        self.log_parse.find_last_log_file_path()
        self.assertEqual(self.log_parse.log_file_path, self.second_file)
        self.assertNotEqual(self.log_parse.log_file_path, self.first_file)

    def test_parse_logfile(self):
        self.log_parse.find_last_log_file_path()
        self.log_parse.parse_logfile()
        self.assertEqual(self.log_parse.get_log(), LOG_DATA)

    def test_parse_log_line(self):
        self.assertEqual(self.log_parse._parse_log_line(self.line_1), self.line_1_result)
        self.assertEqual(self.log_parse._parse_log_line(self.line_2), self.line_2_result)
        self.assertEqual(self.log_parse._parse_log_line(self.line_3), self.line_3_result)
        self.assertNotEqual(self.log_parse._parse_log_line(self.line_3), self.line_3_bad_result)

    def test_get_log_date_name(self):
        self.log_parse.log_file_path = '/nginx-access-ui.log-20170630'
        self.assertEqual(self.log_parse.get_log_date_name(), '20170630')
        self.log_parse.log_file_path = '/nginx-access-ui.log-20170419'
        self.assertEqual(self.log_parse.get_log_date_name(), '20170419')


class ReportTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        log_data = {
                '/url1': [0.123, 0.1, 0.23, 0.233],
                '/url2': [0.5],
                # '/url3': [1.123, 0.02, 0.223, 0.344],
        }
        log = LogParser(Configure())
        log.log = log_data
        all_count = 5
        all_time = 1.186
        self.report_data = [
            {
                'url': '/url2',
                'count': 1,
                'time_max': 0.5,
                'time_sum': 0.5,
                'time_med': 0.5,
                'time_avg': 0.5 / 1,
                'count_perc': round(1.0 / all_count * 100, 4),
                'time_perc': round(0.5 / all_time * 100, 3)
            },
            {
                'url': '/url1',
                'count': 4,
                'time_max': 0.233,
                'time_sum': 0.686,
                'time_med': 0.1,
                'time_avg': 0.686/4,
                'count_perc': round(4.0/all_count*100, 4),
                'time_perc': round(0.686/all_time*100, 3),
            }
        ]
        self.report = Report(log, Configure())

    def test_calculate_report(self):
        self.report.calculate_report()
        self.assertEqual(self.report.report_data, self.report_data)


if __name__ == '__main__':
    unittest.main()
