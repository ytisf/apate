#!/usr/bin/python

import os
import sys
import time
import zlib
import base64
import socket
import argparse


SERVER_ADDR = "SERVERIP"
SERVER_PORT = "SERVERPORT"
REPORT_TIME = 1


def _build_report(content, conf_id):
    conf_string = conf_id + "\n"
    conf_string += base64.b64encode(zlib.compress(content)) + "\n"
    return conf_string


def _get_logfile(conf_id):
    fpath = "/var/logs/winnie/%s.log" % conf_id

    if os.path.isfile(fpath) is False:
        return False
    else:
        try:
            f = open(fpath, 'r')
            content = f.read()
            f.close()
            return content
        except IOError,e:
            return False


def _ping_home():
    try:
        sock = socket.socket()
        sock.settimeout(10)
        sock.connect((SERVER_ADDR, SERVER_PORT))
    except socket.error, e:
        return 'SOCK_CONNECTION_ERR'

    sock.send("ping\n")
    try:
        a = sock.recv(5)
    except socket.timeout:
        sock.close()
        return 'SOCK_TIMEOUT_ERR'
    if "pong" in a:
        sock.close()
        return "PASS"
    else:
        sock.close()
        return "SOCK_RETURN_ERR"


def loopback_report(conf_id):
    cont = _get_logfile(conf_id)
    if cont is False:
        print "No log file found."
        sys.exit(-1)

    err_counter = 0

    try:
        while True:

            if err_counter > 5:
                sys.exit()

            time.sleep(REPORT_TIME)

            content = _get_logfile(conf_id)
            if content is False:
                err_counter += 1
                continue
            else:
                try:
                    sock = socket.socket()
                    sock.connect((SERVER_ADDR, SERVER_PORT))
                    report = _build_report(content, conf_id)
                    sock.send(report)
                    sock.close()
                except:
                    err_counter += 1
                    continue

    except KeyboardInterrupt:
        sys.exit()


def validate_confs(conf_id):
    # Verify Connection
    temp = _ping_home()
    if temp is not "PASS":
        print temp
        sys.exit()

    if _get_logfile(conf_id) is False:
        print "LOGFILE_ERR"
        sys.exit()

    print "PASS"


def parse_arguments():

    global SERVER_PORT

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', help='test settings')
    parser.add_argument('-r', help='start reporting')
    parser.add_argument('-p', help='port')
    args = parser.parse_args()

    if args.p is None:
        print "no port"
        sys.exit()

    try:
        SERVER_PORT = int(args.p)
    except:
        print "server port must be int!"
        sys.exit()

    if args.t is not None and args.r is None:
        validate_confs(args.t)
    elif args.r is not None and args.t is None:
        loopback_report(args.r)
    else:
        return None


if __name__ == "__main__":
    parse_arguments()
