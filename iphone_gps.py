# Process:
#   Not added yet.
#####
# Config:
#   main.plugins.iphone_gps.enabled = true
#   [OPTIONAL] main.plugins.iphone_gps.use_last_loc = true (default: false)
#   [OPTIONAL] main.plugins.linespacing = 15 (default: 10)
#####
# Requirements:
# - None
#####
# Tested on:
#   Hardware:
#   - RPi Zero 2 W
#   - iPhone 7 plus
#   Running: https://github.com/jayofelony/pwnagotchi/releases/tag/v2.8.6

import json
import logging
from flask import jsonify

import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK


class iPhoneGPS(plugins.Plugin):
    __author__ = "xentrify"
    __version__ = "1.0.1"
    __license__ = "GPL3"
    __description__ = "Saves GPS coordinates whenever an handshake is captured. Uses your iPhone's GPS via website requests and Shortcuts."
    # credits to:
    # - evilsocket@gmail.com (Original GPS plugin)
    LINE_SPACING = 10
    LABEL_SPACING = 0

    def __init__(self):
        self.running = False
        self.stop = False
        self.coordinates = dict()
        self.options = dict()
        self.use_last_loc = False

    def on_webhook(self, path, request):
        if not self.running:
            logging.info("[iPhone-GPS] on_webhook called but plugin wasn't running.")
            return "Not running yet"

        if request.method == "GET":
            if path.startswith("send_gps"):
                try:
                    cords = dict()
                    cords["Latitude"] = float(request.args.get("lat"))
                    cords["Longitude"] = float(request.args.get("lon"))
                    cords["Altitude"] = float(request.args.get("alt").replace(",", "."))
                    self.coordinates = cords
                    logging.info(f"[iPhone-GPS] Updated coordinates to: ({cords})")
                    if self.stop:
                        return "stop"
                    else:
                        return ""

                except Exception as exc:
                    logging.info(f"[iPhone-GPS] An error occured while handling the webhook request: {exc}")
                    if self.stop:
                        return "stop"
                    else:
                        return ""
            elif path.startswith("get_gps"):
                if self.coordinates and all(["Latitude" in self.coordinates.keys(), "Longitude" in self.coordinates.keys(), "Altitude" in self.coordinates.keys()]):
                    if self.stop:
                        if "use_last_loc" in self.options:
                            if self.options["use_last_loc"]:
                                return jsonify(self.coordinates)
                            else:
                                return jsonify({})
                        else:
                            return jsonify({})
                    else:
                        return jsonify(self.coordinates)
                else:
                    return jsonify({})

            elif "stop" in path:
                logging.info("[iPhone-GPS] Stopping...")
                self.stop = True
                return ""
            else:
                return ""

    def on_loaded(self):
        logging.info("[iPhone-GPS] Plugin loaded")

    def on_ready(self, agent):
        logging.info("[iPhone-GPS] Plugin ready")
        self.running = True

    def on_ui_setup(self, ui):
        try:
            line_spacing = int(self.options['linespacing'])
        except Exception:
            line_spacing = self.LINE_SPACING

        try:
            pos = self.options['position'].split(',')
            pos = [int(x.strip()) for x in pos]
            lat_pos = (pos[0] + 5, pos[1])
            lon_pos = (pos[0], pos[1] + line_spacing)
            alt_pos = (pos[0] + 5, pos[1] + (2 * line_spacing))
        except Exception:
            if ui.is_waveshare_v2():
                lat_pos = (127, 74)
                lon_pos = (122, 84)
                alt_pos = (127, 94)
            elif ui.is_waveshare_v1():
                lat_pos = (130, 70)
                lon_pos = (125, 80)
                alt_pos = (130, 90)
            elif ui.is_inky():
                lat_pos = (127, 60)
                lon_pos = (122, 70)
                alt_pos = (127, 80)
            elif ui.is_waveshare144lcd():
                lat_pos = (67, 73)
                lon_pos = (62, 83)
                alt_pos = (67, 93)
            elif ui.is_dfrobot_v2():
                lat_pos = (127, 74)
                lon_pos = (122, 84)
                alt_pos = (127, 94)
            else:
                lat_pos = (127, 51)
                lon_pos = (122, 61)
                alt_pos = (127, 71)

        ui.add_element(
            "latitude",
            LabeledValue(
                color=BLACK,
                label="lat:",
                value="-",
                position=lat_pos,
                label_font=fonts.Small,
                text_font=fonts.Small,
                label_spacing=self.LABEL_SPACING,
            ),
        )
        ui.add_element(
            "longitude",
            LabeledValue(
                color=BLACK,
                label="long:",
                value="-",
                position=lon_pos,
                label_font=fonts.Small,
                text_font=fonts.Small,
                label_spacing=self.LABEL_SPACING,
            ),
        )
        ui.add_element(
            "altitude",
            LabeledValue(
                color=BLACK,
                label="alt:",
                value="-",
                position=alt_pos,
                label_font=fonts.Small,
                text_font=fonts.Small,
                label_spacing=self.LABEL_SPACING,
            ),
        )

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('latitude')
            ui.remove_element('longitude')
            ui.remove_element('altitude')

    def on_ui_update(self, ui):
        with ui._lock:
            if self.coordinates and all([
                # avoid 0.000... measurements
                self.coordinates["Latitude"], self.coordinates["Longitude"]
            ]):
                # last char is sometimes not completely drawn ¯\_(ツ)_/¯
                # using an ending-whitespace as workaround on each line
                ui.set("latitude", f"{self.coordinates['Latitude']:.2f} ")
                ui.set("longitude", f"{self.coordinates['Longitude']:.2f} ")
                ui.set("altitude", f"{self.coordinates['Altitude']:.1f}m ")