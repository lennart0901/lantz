import socket
import socketserver

class SimError(Exception):
    pass

def CreateHandlerClass(instrument):

    class Handler(socketserver.StreamRequestHandler):

        instrument = instrument

        TERMINATION = '\n'
        ENCODING = 'ascii'

        CONVERSION = {float: '{:.4f}',
                      int: '{:d}',
                      str: '{}'}

        def handle(self):
            try:
                while True:
                    data = self.rfile.readline()
                    print('{0:s} -> inst: {1}'.format(self.client_address[0], data))
                    data = str(data, self.ENCODING)
                    out = self._dispatch(data)
                    out = self.CONVERSION[type(out)].format(out)
                    out = bytes(out + self.TERMINATION, self.ENCODING)
                    self.wfile.write(out)
                    print('{0:s} <- inst: {1}'.format(self.client_address[0], out))
            except socket.error as e:
                if e.errno == 32: # Broken pipe
                    print('Client disconnected')
            finally:
                self.finish()


        def _dispatch(self, data):
            data = data.strip()
            try:
                sig, value = data[0], data[1:].split()
                prop = value[0].lower()
                current = getattr(self.instrument, prop)
                if isinstance(current, dict):
                    dict_key = getattr(instrument, prop + '_key_convert')(value[1])
                else:
                    dict_key = None

                if sig == '?':
                    if dict_key:
                        return current[dict_key]
                    return current
                elif sig == '!':
                    if dict_key:
                        cls = type(current[dict_key])
                        current[dict_key] = cls(value[2])
                    else:
                        cls = type(current)
                        setattr(instrument, prop, cls(value[1]))
                    return "OK"
                return 'ERROR'
            except (SimError, IndexError) as e:
                return 'ERROR'
            except Exception as e:
                print('Exception {}'.format(e))
                raise Exception

    return Handler

class SimFunctionGenerator(object):

    def __init__(self):
        self._amp = 0.0
        self.fre = 1000.0
        self.off = 0.0
        self._wvf = 0
        self.out = 0
        self.dou = {ch:0 for ch in range(8)}
        self.din = {ch:0 for ch in range(8)}

        self.din_key_convert = int
        self.dou_key_convert = int

    @property
    def idn(self):
        return 'FunctionGenerator Serial #12345'

    @property
    def wvf(self):
        return self._wvf

    @wvf.setter
    def wvf(self, value):
        if value < 0 or value > 3:
            raise SimError
        self._wvf = value

    @property
    def amp(self):
        return self._amp

    @amp.setter
    def amp(self, value):
        if value > 10 or value < 0:
            raise SimError
        self._amp = value




if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 5678

    host = "localhost"

    instrument = SimFunctionGenerator()

    Handler = CreateHandlerClass(instrument)
    
    # Create the server, binding to localhost on port 5678
    server = socketserver.TCPServer((host, port), Handler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    print('Listening to {}:{}'.format(host, port))
    print('interrupt the program with Ctrl-C')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Ending')
    finally:
        server.shutdown()

    #server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    #server_thread.setDaemon(True)
    #server_thread.start()
    #print("Server loop running in thread:", server_thread.name)
    #server.shutdown()
