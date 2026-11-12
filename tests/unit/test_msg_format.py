import logging
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from colorama import Fore
from src.utils import msg_format


class TestMessagingFunctions(unittest.TestCase):
    def setUp(self):
        self.logger = logging.Logger('test-range-provisioner', logging.DEBUG)
        self.logger.propagate = False
        self.patch_logger = patch.object(msg_format, '_logger', self.logger)
        self.patch_logger.start()
        self.addCleanup(self.patch_logger.stop)

    def test_legacy_console_format_and_debug_flag(self):
        output = StringIO()
        with redirect_stdout(output):
            msg_format.error_msg('failure', 'Heat')
            msg_format.general_msg('working', 'Heat')
            msg_format.success_msg('done', 'Heat')
            msg_format.info_msg('hidden', 'Heat')
            msg_format.info_msg({'detail': 1}, 'Heat', True)

        self.assertEqual(
            output.getvalue(),
            f"{Fore.RED}{'Heat'.ljust(12)}{'[ERROR]'.ljust(12)}{Fore.RESET}failure\n"
            f"{Fore.YELLOW}{'Heat'.ljust(12)}{'[INFO]'.ljust(12)}{Fore.RESET}working\n"
            f"{Fore.GREEN}{'Heat'.ljust(12)}{'[SUCCESS]'.ljust(12)}{Fore.RESET}done\n"
            f"{Fore.BLUE}{'Heat'.ljust(12)}{'[INFO]'.ljust(12)}{Fore.RESET}"
            "{'detail': 1}\n",
        )

    def test_existing_logging_handler_receives_records_without_console_duplicate(self):
        output = StringIO()
        with redirect_stdout(output):
            msg_format.general_msg('first', 'Heat')
            captured = StringIO()
            handler = logging.StreamHandler(captured)
            self.logger.addHandler(handler)
            msg_format.error_msg('second', 'Heat')

        self.assertIn('first', output.getvalue())
        self.assertNotIn('second', output.getvalue())
        self.assertEqual(captured.getvalue(), 'second\n')
        self.assertEqual(self.logger.handlers, [handler])

    def test_log_records_expose_levels_endpoint_and_kind(self):
        with self.assertLogs(self.logger, level='DEBUG') as records:
            msg_format.general_msg('normal', 'Heat')
            msg_format.success_msg('complete', 'Swift')
            msg_format.error_msg('failure', 'Guacamole')
            msg_format.info_msg('details', 'Heat', True)
            msg_format.info_msg('suppressed', 'Heat', False)

        self.assertEqual(
            [(record.levelno, record.endpoint, record.message_kind, record.getMessage())
             for record in records.records],
            [
                (logging.INFO, 'Heat', 'general', 'normal'),
                (logging.INFO, 'Swift', 'success', 'complete'),
                (logging.ERROR, 'Guacamole', 'error', 'failure'),
                (logging.DEBUG, 'Heat', 'debug', 'details'),
            ],
        )

    def test_native_logging_records_use_console_handler(self):
        output = StringIO()
        with redirect_stdout(output):
            msg_format.general_msg('start')
            self.logger.warning('native warning')

        self.assertIn('[WARNING]', output.getvalue())
        self.assertIn('native warning', output.getvalue())


if __name__ == '__main__':
    unittest.main()
