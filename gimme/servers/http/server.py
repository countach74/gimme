import sys
from .connection import Connection
from ...errors import FDError
from . import modulemonitor
from ..logger import StdLogger
import select
import socket
import signal


class HTTPServer(object):
    def __init__(self, app, host='localhost', port=8080, listen=5,
            max_read=8092, chunk_size=1024, auto_reload=True,
            logger=StdLogger()):

        self.app = app
        self.host = host
        self.port = port
        self.listen = listen
        self.chunk_size = chunk_size
        self.max_read = max_read
        self.auto_reload = auto_reload
        self.logger = logger

        self.connections = []

        # Setup socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if self.auto_reload:
            self.module_monitor = modulemonitor.ModuleMonitor(self)

        '''
        self.environment = Environment(
            loader=ChoiceLoader([PackageLoader('gimme', 'templates'),
                FileSystemLoader('templates')]))
        '''

        self.running = True

        # Basic lists needed for select
        self.r_list = [self.socket]
        self.w_list = []
        self.e_list = []

    def _bind_socket(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.listen)

    def _handle_signal(self, signum, frame):
        if signum in (signal.SIGTERM, signal.SIGINT):
            self.stop(True)

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def start(self):
        try:
            self._bind_socket()
        except socket.error, e:
            self.logger.log_error("Could not start HTTP Server: %s" %
                e.args[1])
            sys.exit(1)

        self._setup_signal_handlers()

        if self.auto_reload:
            self.module_monitor.start()

        self.logger.log_info("Gimme Asynchronous HTTP Server is now ready")

        while self.running:
            try:
                r_ready, w_ready, e_ready = select.select(self.r_list,
                    self.w_list, self.e_list, 0.01)
            except (select.error, socket.error):
                r_ready, w_ready, e_ready = [], [], []
                self.running = False
            except FDError, e:
                # In this case, a socket has closed prematurely; handle it
                # gracefully and move on
                conn = e.args[0]
                for i in (self.r_list, self.w_list, self.e_list):
                    if conn in i:
                        i.remove(conn)
                r_ready, w_ready, e_ready = [], [], []

            for i in r_ready:
                if i is self.socket:
                    connection = Connection(self, self.socket.accept())
                    self.r_list.append(connection)
                    connection.handle_connect()

                elif isinstance(i, Connection):
                    i.handle_read()

            for i in w_ready:
                i.handle_write()

            for i in e_ready:
                i.handle_error()

    def stop(self, stop_monitor=False):
        self.logger.log_info("Shutting down Gimme HTTP Server...")

        for i in self.connections:
            i.close()
            i.join()

        self.socket.close()

        if stop_monitor and self.auto_reload:
            self.module_monitor.stop()
            self.module_monitor.join()
