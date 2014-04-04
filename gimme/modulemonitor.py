import sys
import time
import datetime
import os
import gevent
import gevent.event


class ModuleMonitor(gevent.Greenlet):
    '''
    Monitors all of the modules loaded by the current running application. If
    any of them change (detected via os.stat), reload the running process.
    '''
    def __init__(self, server, interval=1):
        self.server = server
        self.interval = interval
        self._stop = gevent.event.Event()
        gevent.Greenlet.__init__(self)

    def _run(self):
        print 'Starting module monitor...'
        datetime.datetime.now()
        last_scan = datetime.datetime.now()

        old_stats = self.stat_modules()

        while not self.stopped():
            now = datetime.datetime.now()
            delta = datetime.timedelta(seconds=self.interval)
            if now > last_scan + delta:
                new_stats = self.stat_modules()
                if not self.compare_stats(old_stats, new_stats):
                    print 'Something changed! Restarting server...'
                    self.server.stop()
                    gevent.sleep(1)
                    self.restart_app()
                old_stats = new_stats
            gevent.sleep(1)

    def restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def stopped(self):
        return self._stop.is_set()

    def stop(self):
        self._stop.set()

    def compare_stats(self, old, new):
        '''
        Returns true if the two stat dictionaries don't differ, false
        if they do.
        '''
        for key, value in old.iteritems():
            if key in new and new[key].st_mtime != value.st_mtime:
                return False
        return True

    def stat_modules(self):
        stats = {}
        for name, module in sys.modules.items():
            try:
                path = module.__file__
            except AttributeError:
                continue

            try:
                stats[path] = os.stat(path)
            except EnvironmentError:
                pass

            try:
                path = path[:-1]
                stats[path] = os.stat(path)
            except EnvironmentError:
                pass

        return stats
