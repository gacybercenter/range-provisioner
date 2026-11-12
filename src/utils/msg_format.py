"""Compatibility helpers for Range Provisioner log messages."""

import logging
import sys

from colorama import Fore


_logger = logging.getLogger('range_provisioner')
if _logger.level == logging.NOTSET:
    _logger.setLevel(logging.DEBUG)


class _ConsoleHandler(logging.StreamHandler):
    """Write to the current stdout, including when it is redirected."""

    _range_provisioner_default = True

    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stdout
        super().emit(record)


class _ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        kind = getattr(record, 'message_kind', None)
        endpoint = getattr(record, 'endpoint', '')
        endpoint = endpoint.ljust(12) if endpoint else ''
        styles = {
            'error': (Fore.RED, '[ERROR]'),
            'debug': (Fore.BLUE, '[INFO]'),
            'success': (Fore.GREEN, '[SUCCESS]'),
            'general': (Fore.YELLOW, '[INFO]'),
        }
        if kind in styles:
            color, label = styles[kind]
        else:
            color = Fore.RED if record.levelno >= logging.ERROR else Fore.YELLOW
            label = f'[{record.levelname}]'
        return f'{color}{endpoint}{label.ljust(12)}{Fore.RESET}{record.getMessage()}'


def _log(level: int, kind: str, text: str | list | dict, endpoint: str) -> None:
    default_handlers = [
        handler for handler in _logger.handlers
        if getattr(handler, '_range_provisioner_default', False)
    ]
    other_handlers = any(
        not getattr(handler, '_range_provisioner_default', False)
        for handler in _logger.handlers
    )
    ancestor_handlers = (
        _logger.propagate
        and _logger.parent is not None
        and _logger.parent.hasHandlers()
    )
    if other_handlers or ancestor_handlers:
        for handler in default_handlers:
            _logger.removeHandler(handler)
            handler.close()
    elif not default_handlers:
        handler = _ConsoleHandler()
        handler.setFormatter(_ConsoleFormatter())
        _logger.addHandler(handler)

    _logger.log(level, '%s', text, extra={'endpoint': endpoint, 'message_kind': kind})


def error_msg(text: str | list | dict, endpoint: str = '') -> None:
    _log(logging.ERROR, 'error', text, endpoint)


def info_msg(text: str | list | dict, endpoint: str = '', debug: bool = False) -> None:
    if debug:
        _log(logging.DEBUG, 'debug', text, endpoint)


def success_msg(text: str | list | dict, endpoint: str = '') -> None:
    _log(logging.INFO, 'success', text, endpoint)


def general_msg(text: str | list | dict, endpoint: str = '') -> None:
    _log(logging.INFO, 'general', text, endpoint)
