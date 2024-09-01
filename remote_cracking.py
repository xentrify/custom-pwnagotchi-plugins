import ftplib
import os
import logging
import traceback
from threading import Lock
from json.decoder import JSONDecodeError
from ftplib import FTP_TLS
from io import BytesIO

import pwnagotchi.ui.fonts as fonts
from pwnagotchi.utils import StatusFile, remove_whitelisted
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
from pwnagotchi import plugins


class RemoteCracking(plugins.Plugin):
    __author__ = "xentrify"
    __version__ = "1.0.0"
    __license__ = "GPL3"
    __description__ = "This plugin automatically uploads handshakes to your FTP cracking server."
    # credits to:
    # - junohea.mail@gmail.com (hashie-hcxpcapngtool)
    # - @nagy_craig (display-password)
    # - 33197631+dadav@users.noreply.github.com (wpa-sec)

    def __init__(self):
        self.ready = False
        self.lock = Lock()
        try:
            self.report = StatusFile("/root/.remote_cracking_uploads", data_format="json")
        except JSONDecodeError:
            logging.warning("[RemoteCracking] Failed to load upload report file. Removing it and starting again.")
            os.remove("/root/.remote_cracking_uploads")
            self.report = StatusFile("/root/.remote_cracking_uploads", data_format="json")

        self.ftp_server = str()
        self.ftp_port = int()
        self.ftp_user = str()
        self.ftp_passwd = str()

        self.options = dict()
        self.display_cracked = bool()
        self.potfile = str()
        self.skip = list()
        self.last_cracked = dict()

    def on_loaded(self):
        if "port" in self.options and self.options["port"]:
            try:
                self.ftp_port = int(self.options["port"])
            except ValueError:
                logging.error("[RemoteCracking] The port is not set correctly, it has to be digits only.")
                return
        else:
            logging.error("[RemoteCracking] The port is not set.")
            return

        if "server" in self.options and self.options["server"]:
            self.ftp_server = (self.options["server"]).strip()
        else:
            logging.error("[RemoteCracking] The server is not set.")
            return

        self.ftp_user = self.options["user"] if "user" in self.options else None
        self.ftp_passwd = self.options["password"] if "password" in self.options else None

        if not self.ftp_user or not self.ftp_passwd:
            logging.warning("[RemoteCracking] User and/or password are not set.")
            return

        self.display_cracked = self.options["display_cracked"] if "display_cracked" in self.options else True
        self.potfile = self.options["potfile"] if "potfile" in self.options else "/root/remote_cracking.potfile"
        self.ready = True
        logging.info("[RemoteCracking] Plugin loaded successfully.")

    # def on_webhook(self, path, request):
    #     from flask import make_response, redirect
    #     response = make_response(redirect(self.options["api_url"], code=302))
    #     response.set_cookie("key", self.options["api_key"])
    #     return response

    def on_internet_available(self, agent):
        if not self.ready or self.lock.locked():
            return

        with self.lock:
            config = agent.config()
            display = agent.view()
            reported = self.report.data_field_or("reported", default=list())
            handshake_dir = config["bettercap"]["handshakes"]
            handshake_filenames = os.listdir(handshake_dir)
            handshake_paths = [os.path.join(handshake_dir, filename) for filename in handshake_filenames if
                               filename.endswith(".22000")]
            handshake_paths = remove_whitelisted(handshake_paths, self.options["whitelist"])
            handshake_new = set(handshake_paths) - set(reported) - set(self.skip)
            ftps = FTP_TLS()
            ftps.connect(self.ftp_server, self.ftp_port)

            ftps.login(self.ftp_user, self.ftp_passwd)
            ftps.prot_p()
            if handshake_new:
                logging.info("[RemoteCracking] New handshakes detected, starting upload.")
                for idx, handshake in enumerate(handshake_new):
                    display.on_uploading(f"RemoteCracking ({idx + 1}/{len(handshake_new)})")
                    try:
                        with open(handshake, "rb") as file:
                            ftps.storbinary(f"STOR {os.path.basename(handshake)}", file)
                        reported.append(handshake)
                        self.report.update(data={"reported": reported})
                        logging.info(f"[RemoteCracking] Uploaded {handshake} successfully.")

                    except ftplib.all_errors as e:
                        logging.warning("[RemoteCracking] Error occured while uploading file, traceback:")
                        logging.warning(traceback.format_exc())

                    except Exception as e:
                        logging.warning("[RemoteCracking] Error occured while uploading file, traceback:")
                        logging.warning(traceback.format_exc())

            if self.display_cracked:
                try:
                    files = ftps.nlst()
                    if "cracked.txt" in files:
                        r = BytesIO()
                        ftps.retrbinary('RETR cracked.txt', r.write)
                        content = (r.getvalue()).decode("utf-8").replace("\r", "")
                        with open(self.potfile, "w+") as file:
                            file.write(content)
                        # lines = [line for line in (r.getvalue()).decode("utf-8").replace("\r", "").split("\n") if line.strip() != ""]
                        # self.last_cracked = ":".join(line for line in lines[-1].split(":")[-2:])
                        # logging.warning(self.last_cracked)
                except ftplib.all_errors as e:
                    logging.warning("[RemoteCracking] Error occured while downloading file, traceback:")
                    logging.warning(traceback.format_exc())
                except Exception as e:
                    logging.warning("[RemoteCracking] Error occured while downloading/writing file, traceback:")
                    logging.warning(traceback.format_exc())
            ftps.quit()
            display.on_normal()

    def on_ui_setup(self, ui):
        if not self.display_cracked:
            return
        #line_spacing = int(self.options["line_spacing"]) if "line_spacing" in self.options else self.LINE_SPACING
        #label_spacing = int(self.options["label_spacing"]) if "label_spacing" in self.options else self.LABEL_SPACING
        orientation = self.options["orientation"] if "orientation" in self.options else "horizontal"
        pos = None
        if "position" in self.options:
            try:
                pos = [int(x.strip()) for x in self.options["position"].split(",")]
                if not len(pos) >= 2:
                    logging.error("[RemoteCracking] Could not process set position, using default.")
                elif len(pos) > 2:
                    logging.error("[RemoteCracking] Too many positions set (only two are needed: x,y), using the first two.")
                    pos = (pos[0], pos[1])
                else:
                    pos = (pos[0], pos[1])
            except Exception:
                logging.error("[RemoteCracking] Could not process set position, using default.")
        else:
            if orientation == "vertical":
                pos = (180, 61)
            else:
                pos = (0, 91)
        ui.add_element('remote-cracking', LabeledValue(color=BLACK, label='', value='',
                                                       position=pos,
                                                       label_font=fonts.Bold, text_font=fonts.Small, label_spacing=0))


    def on_ui_update(self, ui):
        if not self.display_cracked:
            return
        if os.path.exists(self.potfile):
            with open(self.potfile) as file:
                lines = file.read().splitlines()
                if lines and len(lines) > 0:
                    self.last_cracked = ":".join(line for line in lines[-1].split(":")[-2:])
        ui.set("remote-cracking", self.last_cracked if self.last_cracked else "")
