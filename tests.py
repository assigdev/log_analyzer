import unittest
import os
import errno
import shutil
from tests_fixtures.data import LOG_DATA, LOG_FILE_DATA
from log_analyzer import config, calculate_report, parse_logfile
from log_analyzer import find_last_log_file_path, get_log_date_name, parse_log_line


class FindLastLogFilePathTestCase(unittest.TestCase):
    def setUp(self):
        self.path = 'test_log'
        self.conf = config.copy()
        self.conf['LOG_DIR'] = self.path
        try:
            os.makedirs(self.path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.first_file = self.path+"/nginx-access-ui.log-20170630"
        self.second_file = self.path+"/nginx-access-ui.log-20170631"
        f1 = open(self.first_file, 'a')
        f1.close()
        f2 = open(self.second_file, 'a')
        f2.close()

    def tearDown(self):
        shutil.rmtree(self.conf['LOG_DIR'])

    def test_find_last_log_file_path(self):
        self.assertEqual(find_last_log_file_path(self.conf), self.second_file)
        self.assertNotEqual(find_last_log_file_path(self.conf), self.first_file)


class ParseLogfileTestCase(unittest.TestCase):
    def setUp(self):

        self.path = 'test_log'
        try:
            os.makedirs(self.path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.log_file_path = self.path + "/nginx-access-ui.log-20170630"
        f = open(self.log_file_path, 'a')
        f.write(LOG_FILE_DATA)
        f.close()

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_parse_logfile(self):
        self.assertEqual(parse_logfile(self.log_file_path, config), LOG_DATA)


class ParseLogLine(unittest.TestCase):
    def setUp(self):
        self.line_1 = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
        self.line_1_result = '/api/v2/banner/25019354', 0.390
        self.line_2 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199'
        self.line_2_result = '/api/v2/banner/16852664', 0.199
        self.line_3 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/1717161 HTTP/1.1" 200 2116 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752771" "712e90144abee9" 0.138'
        self.line_3_result = '/api/v2/banner/1717161', 0.138
        self.line_3_bad_result = '/api/v2/banner/1717161', 0.136

    def test_parse_log_line(self):
        self.assertEqual(parse_log_line(self.line_1, config), self.line_1_result)
        self.assertEqual(parse_log_line(self.line_2, config), self.line_2_result)
        self.assertEqual(parse_log_line(self.line_3, config), self.line_3_result)
        self.assertNotEqual(parse_log_line(self.line_3, config), self.line_3_bad_result)


class GetLogDateNameTestCase(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            '/nginx-access-ui.log-20170630': '20170630',
            '/nginx-access-ui.log-20170419': '20170419',
        }

    def test_get_log_date_name(self):
        for key in self.test_data:
            self.assertEqual(get_log_date_name(key), self.test_data[key])


class CalculateReportTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.log_data = {
                '/url1': [0.123, 0.1, 0.23, 0.233],
                '/url2': [0.5],
                '/url3': [1.1, 0.1, 0.2, 0.4, 0.3],
        }
        all_count = 10
        all_time = 3.286
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
                'url': '/url3',
                'count': 5,
                'time_max': 1.1,
                'time_sum': 2.1,
                'time_med': 0.3,
                'time_avg': round(2.1 / 5, 3),
                'count_perc': round(5.0 / all_count * 100, 4),
                'time_perc': round(2.1 / all_time * 100, 3)
            },
            {
                'url': '/url1',
                'count': 4,
                'time_max': 0.233,
                'time_sum': 0.686,
                'time_med': 0.1765,
                'time_avg': 0.686/4,
                'count_perc': round(4.0/all_count*100, 4),
                'time_perc': round(0.686/all_time*100, 3),
            }
        ]

    def test_calculate_report(self):
        self.assertEqual(calculate_report(self.log_data, config), self.report_data)


if __name__ == '__main__':
    unittest.main()
