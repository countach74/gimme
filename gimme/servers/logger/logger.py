__all__ = ['SysLogger', 'StdLogger']

import abc
import sys
import syslog
import datetime


class BaseLogger(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _log_message(self, level, message):
        pass

    def log_info(self, message):
        self._log_message(syslog.LOG_INFO, message)

    def log_warn(self, message):
        self._log_message(syslog.LOG_WARNING, message)

    def log_crit(self, message):
        self._log_message(syslog.LOG_CRIT, message)

    def log_notice(self, message):
        self._log_message(syslog.LOG_NOTICE, message)

    def log_error(self, message):
        self._log_message(syslog.LOG_ERR, message)

    def log_emergency(self, message):
        self._log_message(syslog.LOG_EMERG, message)

    def log_alert(self, message):
        self._log_message(syslog.LOG_ALERT, message)


class SysLogger(BaseLogger):
    def __init__(self, ident='gimme'):
        syslog.openlog(ident)

    def _log_message(self, level, message):
        syslog.syslog(level, message)


class StdLogger(BaseLogger):
    _level_map = {
        syslog.LOG_INFO: 'info',
        syslog.LOG_WARNING: 'warning',
        syslog.LOG_CRIT: 'critical',
        syslog.LOG_NOTICE: 'notice',
        syslog.LOG_ERR: 'error',
        syslog.LOG_EMERG: 'emergency',
        syslog.LOG_ALERT: 'alert'
    }

    def _log_message(self, level, message):
        timestamp = datetime.datetime.now().strftime('%a %b %d %Y %H:%M:%S.%f')
        level_string = self._level_map[level]
        sys.stderr.write("[%s] [%s] %s\n" % (timestamp, level_string, message))
