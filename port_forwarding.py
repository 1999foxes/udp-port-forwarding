import sys
import socket
import socketserver
import threading
from time import sleep

src_ip = sys.argv[1]
src_port = sys.argv[2]
dst_ip = sys.argv[3]
dst_port = sys.argv[4]


def run_thr_svr(svr):
    thr = threading.Thread(target=svr.serve_forever)
    thr.daemon = True
    thr.start()
    return thr


def stop_serve(svr):
    sleep(.1)
    svr.shutdown()
    svr.server_close()


class Dummy(socketserver.BaseRequestHandler):
    DST_ADDR = (dst_ip, dst_port)
    DST_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def handle(self):
        d = self.request[0]
        s = self.request[1]
        if not d:
            return
        self.send_unblock()
        print('send', d, 'from', self.client_address, 'to', self.DST_ADDR)
        self.DST_SOCK.sendto(d, self.DST_ADDR)
        while True:
            try:
                r, dsrv = self.DST_SOCK.recvfrom(4096)
            except socket.error as e:
                if e.errno == 10054:
                    return
                else:
                    raise
            if dsrv[0] == '127.0.0.1':
                return
            if r:
                print('send', r, 'from', dsrv, 'to', self.client_address)
                s.sendto(r, self.client_address)

    def send_unblock(self):
        try:
            addr = self.DST_SOCK.getsockname()
        except socket.error as e:
            if e.errno == 10022:
                return
            else:
                raise
        self.DST_SOCK.sendto('unblock'.encode('utf8'), ('localhost', addr[1]))


if __name__ == '__main__':
    print('udp port forwarding from', src_ip, src_port, 'to', dst_ip, dst_port)
    srv = socketserver.ThreadingUDPServer((src_ip, src_port), Dummy)
    run_thr_svr(srv)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        stop_serve(srv)
        print('\nclose')
