import unittest
import os
import errno
import shutil
from tests_fixtures.data import LOG_DATA
from log_analyzer import \
    get_last_log_file, \
    parse_log_line,\
    get_log_from_logfile, \
    config


class TestGetLastLogFile(unittest.TestCase):
    def setUp(self):
        path = "test_log"
        config["LOG_DIR"] = path
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        first_file = path+"/test_file_first.txt"
        self.last_file = path+"/test_fil_last.txt"
        f1=open(first_file, 'a')
        f1.close()
        f2 = open(self.last_file, 'a')
        f2.close()

    def tearDown(self):
        shutil.rmtree(config["LOG_DIR"])

    def test_func_result(self):
        self.assertEqual(get_last_log_file(), self.last_file)


class TestGetLogFromFile(unittest.TestCase):
    def setUp(self):
        self.log_filename = './tests_fixtures/log_file'

    def test_func_result(self):
        self.assertEqual(get_log_from_logfile(self.log_filename), LOG_DATA)


class TestParseLogFile(unittest.TestCase):
    def setUp(self):
        self.line_1 = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'
        self.line_1_result = '/api/v2/banner/25019354', 0.390
        self.line_2 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199'
        self.line_2_result = '/api/v2/banner/16852664', 0.199
        self.line_3 = '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/1717161 HTTP/1.1" 200 2116 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752771" "712e90144abee9" 0.138'
        self.line_3_result = '/api/v2/banner/1717161', 0.138

    def test_line_1(self):
        self.assertEqual(parse_log_line(self.line_1), self.line_1_result)

    def test_line_2(self):
        self.assertEqual(parse_log_line(self.line_2), self.line_2_result)

    def test_line_3(self):
        self.assertEqual(parse_log_line(self.line_3), self.line_3_result)


if __name__ == '__main__':
    unittest.main()
