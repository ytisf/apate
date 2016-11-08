
import zlib
import base64
import socket
from threading import Thread
from apate.core.aux import _analyzeLogFile
from apate.core.snitch import LogMe, INFORMATION, SUCCESS, WARNING, ERROR


class GoldenRetriver():

    def __init__(self, honey_id, port):
        self.honey_id = honey_id
        self.port = port

    def _parse_input(self, data):
        new = data.split("\n")
        try:
            configurations_id = int(new[0])
        except ValueError:
            LogMe(caller=__name__, m_type=WARNING, message="Input provided from %s does not break into an integer." % self.honey_id)
            return False
        if int(configurations_id) == int(self.honey_id):
            try:
                debase = base64.b64decode(new[1])
                decomp = zlib.decompress(debase)
            except:
                LogMe(caller=__name__, m_type=WARNING, message="Input provided from %s does not break into base64." % self.honey_id)
                return False
            _analyzeLogFile(logdata=decomp,conf_id=self.honey_id)
            return True

        else:
            LogMe(caller=__name__, m_type=WARNING, message="id %s, %s does not match %s, %s" % (configurations_id, type(configurations_id),self.honey_id, type(self.honey_id)))
            return False

    def _recvall(self, conn):
        data = ""
        part = None

        while part != "":
            part = conn.recv(4096)
            data += part
        return data

    def _listener(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ('', self.port)
        self.sock.bind(server_address)
        self.sock.listen(1)

        LogMe(caller=__name__, m_type=INFORMATION, message="Now listening for incoming data on %s." % self.port)

        try:
            while True:
                connection, client_address = self.sock.accept()
                try:
                    while True:
                        data = self._recvall(connection)
                        if data:
                            if len(data) < 10 and "ping" in data:
                                connection.sendall("pong\n")
                                connection.close()
                                break
                            else:
                                LogMe(caller=__name__, m_type=SUCCESS, message="Incoming data set from honeypot ID: %s." % self.honey_id)
                                self._parse_input(data)
                                connection.close()
                                break
                        else:
                            break
                finally:
                    connection.close()
        except KeyboardInterrupt:
            self.sock.close()
            return

    def StartListening(self):
        self._listener()

    def KillItDeadJohnny(self):
        self.sock.close()
        self.thread.join()
        return

if __name__ == "__main__":
    a = GoldenRetriver(1234, 1234)
    a.StartListening()
