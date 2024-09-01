import traceback
import logging
import argparse
import subprocess
import json
import sys
import os
import threading
import queue
import time
import datetime
import socket
import requests

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from pyftpdlib.log import config_logging

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--interval", default=5, type=int, required=False,
                        help="Interval between checking for new handshakes in seconds (default: 5)")

    builtin_server = parser.add_argument_group("Builtin FTP Server Settings")
    builtin_server.add_argument("-p", "--port", default=8888, type=int, required=False,
                            help="Port of the FTP server (default: port)")
    builtin_server.add_argument("-U", "--user", default="user", type=str, required=False,
                            help="Username of the FTP server (default: user)")
    builtin_server.add_argument("-P", "--password", type=str, required=True,
                            help="Password of the FTP server (required due to safety)")
    builtin_server.add_argument("-d", "--directory", type=str, required=True,
                                help="Directory of the FTP server")

    builtin_server.add_argument("-c", "--cert-file", type=str, required=True,
                                help="Path to the cert file (required)", dest="cert")
    builtin_server.add_argument("-k", "--key-file", type=str, required=True,
                                help="Path to the key file (required)", dest="key")

    cracking = parser.add_argument_group("Cracking Settings")
    cracking.add_argument("-I", "--interpreter", type=str, required=True,
                          help="Interpreter of hashcat (required)")
    cracking.add_argument("-w", "--wordlists", type=str, required=True,
                          help="Wordlist(s) used for cracking, can be one file or a directory (required)")

    args = parser.parse_args()
    return args
class FTPClass:
    def __init__(self, port, user, password, directory, cert, key, public_ip, local_ip):
        self.port = port
        self.user = user
        self.password = password
        self.directory = directory

        self.public_ip = public_ip
        self.local_ip = local_ip
        self.cert = cert
        self.key = key
        self.server = ThreadedFTPServer
        self.stop = False

    def run(self):
        authorizer = DummyAuthorizer()
        authorizer.add_user(self.user, self.password, self.directory, perm='rlafw')

        handler = TLS_FTPHandler
        handler.certfile = self.cert
        handler.keyfile = self.key
        handler.authorizer = authorizer
        handler.tls_control_required = True
        handler.tls_data_required = True
        handler.banner = "pyftpdlib based ftpd ready."

        handler.masquerade_address = self.public_ip
        handler.passive_ports = range(49152, 65534)
        config_logging(level=logging.ERROR)

        address = (self.local_ip, self.port)
        server = ThreadedFTPServer(address, handler)
        server.max_cons = 10
        server.max_cons_per_ip = 0
        self.server = server
        self.server.serve_forever()

class CrackingClass():
    def __init__(self, interpreter, wordlists, interval, directory, data_file, out_file):
        self.interpreter = interpreter
        self.wordlists = wordlists
        self.interval = interval
        self.directory = directory
        self.data_file = data_file
        self.out_file = out_file

        self.queue = queue.Queue(100)
        self.cracking = False
        self.stop_cracking = False
        self.stop_running = False
        self.last_cracked = dict()
        self.last_data = dict()
    def run(self):
        try:
            with open(self.data_file, "r") as data_file:
                old = [line for line in data_file.read().splitlines() if line.strip() != ""]
        except Exception as e:
            #print("Failed to load data_file!")
            old = []
        while not self.stop_running:
            new = [os.path.join(self.directory, path) for path in os.listdir(self.directory)]
            new_files = [file for file in new if file not in old]
            for file in new_files:
                if file.strip().endswith(".hc22000") or file.strip().endswith(".22000"):
                    self.queue.put(file)
            old = new
            time.sleep(self.interval)


    def cracking_thread(self):
        while not self.stop_cracking:
            self.cracking = False
            try:
                file = self.queue.get(timeout=4)
            except queue.Empty:
                continue
            try:
                proc = subprocess.Popen([self.interpreter, "-o", self.out_file, "--potfile-disable", "--status", "--status-json", "--status-timer=1", "-m", "22000", file, self.wordlists], cwd=os.path.dirname(self.interpreter), stdout=subprocess.PIPE)
                self.cracking = True
                while not self.stop_cracking:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    try:
                        data = json.loads(line.decode("utf-8"))
                        self.last_data = data

                    except:
                        pass
                if self.stop_cracking:
                    proc.terminate()
            except Exception:
                pass
            finally:
                with open(self.data_file, "a") as data_file:
                    data_file.write(file + "\n")
                if os.path.exists(self.out_file):
                    with open(self.out_file) as out_file:
                        lines = [line for line in out_file.readlines() if line.strip() != ""]
                        if len(lines) > 0:
                            last_line = lines[-1]
                            ssid = last_line.split(":")[-2]
                            password = last_line.split(":")[-1]
                            self.last_cracked = {ssid: password}
                        else:
                            pass
                self.queue.task_done()

def clear():
    os.system("cls" if os.name == "nt" else "clear")

class colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[93m"
    BOLD = "\033[1m"
    CLEAR = "\033[0m"

if __name__ == '__main__':
    args = parse_args()
    for path in [args.wordlists, args.directory, args.interpreter]:
        if not os.path.exists(path):
            print(f"{colors.BOLD}{colors.RED}The set wordlist path does not exist!{colors.CLEAR}")
            sys.exit()

        if os.path.isdir(args.wordlists) and not os.listdir(args.wordlists):
            print(f"{colors.BOLD}{colors.RED}The wordlist directory was set correctly, but no files were found!{colors.CLEAR}")
            sys.exit()

    public_ip = None
    try:
        public_ip = requests.get('https://checkip.amazonaws.com').text.strip()
    except Exception as e:
        print(f"{colors.BOLD}{colors.RED}An error occured while fetching the public IP, traceback:{colors.CLEAR}{colors.RED}\n")
        print(traceback.format_exc())
        print(colors.CLEAR)
        sys.exit()

    local_ip = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception as e:
        print(f"{colors.BOLD}{colors.RED}An error occured while fetching the local IP, traceback:{colors.CLEAR}{colors.RED}\n")
        print(traceback.format_exc())
        print(colors.CLEAR)
        sys.exit()

    ftp_server = FTPClass(args.port, args.user, args.password, args.directory, args.cert, args.key, public_ip, local_ip)
    ftp_thread = threading.Thread(target=ftp_server.run)
    ftp_thread.start()
    cracking_class = CrackingClass(args.interpreter, args.wordlists, args.interval, args.directory, os.path.join(args.directory, "data.txt"), os.path.join(args.directory, "cracked.txt"))
    cracking_run_thread = threading.Thread(target=cracking_class.run)
    cracking_run_thread.start()
    cracking_thread = threading.Thread(target=cracking_class.cracking_thread)
    cracking_thread.start()

    while True:
        try:
            clear()
            print(f"{colors.BLUE}Cracking: {colors.GREEN if cracking_class.cracking else colors.RED}{cracking_class.cracking}{colors.CLEAR}", end="")
            print(f" {colors.BOLD}|{colors.CLEAR} ", end="")
            print(f"{colors.BLUE}Queue: {colors.GREEN if cracking_class.queue.qsize() > 0 else colors.RED}{cracking_class.queue.qsize()}")

            data = cracking_class.last_data
            if cracking_class.cracking:
                data = cracking_class.last_data
                start = datetime.datetime.fromtimestamp(data['time_start']) if "time_start" in data else None
                est_stop = datetime.datetime.fromtimestamp(data['estimated_stop']) if "estimated_stop" in data else None
                target = data['target'] if 'target' in data else None

                print(f"{colors.BLUE}Target: {colors.GREEN if target else colors.RED}{target}")
                print(f"{colors.BLUE}Wordlist(s): {colors.GREEN}{cracking_class.wordlists}")

                start = datetime.datetime.fromtimestamp(data['time_start']) if "time_start" in data else None
                est_stop = datetime.datetime.fromtimestamp(data['estimated_stop']) if "estimated_stop" in data else None

                if all([start, est_stop]):

                    if start + datetime.timedelta(hours=23, minutes=59, seconds=59) > est_stop:
                        print(f"{colors.BLUE}Start: {colors.CYAN}{start.time()}{colors.CLEAR}", end="")
                        print(f" {colors.BOLD}|{colors.CLEAR} ", end="")
                        print(f"{colors.BLUE}Est. Stop: {colors.CYAN}{est_stop.time()}")

                    else:
                        print(f"{colors.BLUE}Start: {colors.CYAN}{start}{colors.CLEAR}", end="")
                        print(f" {colors.BOLD}|{colors.CLEAR} ", end="")
                        print(f"{colors.BLUE}Est. Stop: {colors.CYAN}{est_stop}")

                else:
                    print(f"{colors.BLUE}Start: {colors.RED}None{colors.CLEAR}", end="")
                    print(f" {colors.BOLD}|{colors.CLEAR} ", end="")
                    print(f"{colors.BLUE}Est. Stop: {colors.RED}None")

                print(f"{colors.BLUE}Progress: {colors.CYAN}{str(round(data['progress'][0] / data['progress'][1] * 100, 2)) if 'progress' in data else '0'}%", end="")
                print(f" {colors.BOLD}|{colors.CLEAR} ", end="")

            (ssid, password), = cracking_class.last_cracked.items() if cracking_class.last_cracked else [(None, None)]
            color = colors.RED if not ssid or not password else colors.GREEN
            print(f"{colors.BLUE}Last Cracked: {color}{ssid}{colors.CLEAR}:{color}{password}{colors.CLEAR}", end="")
            print(colors.CLEAR)

            # Add display the public/local IP

            time.sleep(1)
        except KeyboardInterrupt:
            print(f"{colors.BOLD}Stopping cracking thread...{colors.CLEAR}")
            cracking_class.stop_cracking = True
            cracking_thread.join()
            print(f"{colors.BOLD}Stopping queue thread...{colors.CLEAR}")
            cracking_class.stop_running = True
            cracking_run_thread.join(timeout=10)
            print(f"{colors.BOLD}Stopping FTP Server thread...{colors.CLEAR}")
            ftp_server.server.close_all()
            ftp_thread.join(timeout=10)
            break
        except Exception as e:
            print(colors.RED + traceback.format_exc() + colors.CLEAR)
    sys.exit()
