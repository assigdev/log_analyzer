import unittest
import os
import errno
import shutil
from tests_fixtures.data import LOG_DATA, LOG_FILE_DATA, LOG_FILE_WRONG_DATA, LOG_WRONG_DATA, LOG_FILE_WRONG_DATA_ERRORS
from log_analyzer import config, calculate_report, parse_logfile
from log_analyzer import find_last_log_file, parse_log_line


class FindLastLogFilePathTestCase(unittest.TestCase):
    def setUp(self):
        self.path = 'test_log'
        self.path2 = 'test_log_null'
        try:
            os.makedirs(self.path)
            os.makedirs(self.path2)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.first_file = self.path+"/nginx-access-ui.log-20170630.txt"
        self.second_file = self.path+"/nginx-access-ui.log-20170631.log"
        f1 = open(self.first_file, 'a')
        f1.close()
        f2 = open(self.second_file, 'a')
        f2.close()

    def tearDown(self):
        shutil.rmtree(self.path)
        shutil.rmtree(self.path2)

    def test_find_last_log_file_path(self):
        self.assertEqual(find_last_log_file(self.path).path, self.second_file)
        self.assertNotEqual(find_last_log_file(self.path).path, self.first_file)
        self.assertIsNotNone(find_last_log_file(self.path))

    def test_not_log_file(self):
        self.assertIsNone(find_last_log_file(self.path2))


class ParseLogfileTestCase(unittest.TestCase):
    def setUp(self):

        self.path = 'test_log'
        self.bad_gzip_path = './tests_fixtures/bad_gz.gz'
        try:
            os.makedirs(self.path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.log_file_path = self.path + "/nginx-access-ui.log-20170630"
        self.log_file_path2 = self.path + "/nginx-access-ui.log-20170631"
        self.log_file_path3 = self.path + "/nginx-access-ui.log-20170731"
        f = open(self.log_file_path, 'a')
        f.write(LOG_FILE_DATA)
        f.close()
        f2 = open(self.log_file_path2, 'a')
        f2.write(LOG_FILE_WRONG_DATA)
        f2.close()
        f3 = open(self.log_file_path3, 'a')
        f3.write(LOG_FILE_WRONG_DATA_ERRORS)
        f3.close()

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_parse_logfile(self):
        self.assertEqual(parse_logfile(self.log_file_path), LOG_DATA)

    def test_parse_wrong_data_max_percent_of_errors(self):
        with self.assertRaises(Exception) as context:
            parse_logfile(self.log_file_path3)
        self.assertTrue('file broken' in context.exception)

    def test_parse_wrong_data(self):
        self.assertEqual(parse_logfile(self.log_file_path2), LOG_WRONG_DATA)

    def test_bad_gzip_open(self):
        with self.assertRaises(Exception) as context:
            parse_logfile(self.bad_gzip_path)
        print context.exception
        self.assertTrue('Not a gzipped file' in context.exception)


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
        self.assertEqual(parse_log_line(self.line_1), self.line_1_result)
        self.assertEqual(parse_log_line(self.line_2), self.line_2_result)
        self.assertEqual(parse_log_line(self.line_3), self.line_3_result)
        self.assertNotEqual(parse_log_line(self.line_3), self.line_3_bad_result)


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
        self.assertEqual(calculate_report(self.log_data, config['REPORT_SIZE']), self.report_data)


if __name__ == '__main__':
    unittest.main()
