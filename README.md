# Custom Pwnagotchi Plugins
This repository contains all of my custom-made pwnagotchi plugins (the ones that were finished). You can set them up using the following guide(s) or if you know what to do, the setup is also included in each file. If you found any bugs or have an issue, you can report them [here](https://github.com/xentrify/custom-pwnagotchi-plugins/issues/new/choose) or on [reddit](https://reddit.com/u/xentrifydev). Also reach out to me if you have any suggestions or ideas for new plugins, I would love to hear them!

---

<br>

## Todo

- [X] Release a new plugin! ([Thread](https://discord.com/channels/717817147853766687/1278003598416019518))
- [ ] Rewrite iPhone_GPS using [GPS_more](https://github.com/Sniffleupagus/pwnagotchi_plugins/blob/main/gps_more.py) + fix it
- [ ] Fix package checking (aftershake)

---

<br>

## Where to find the stuff

- [Plugin Installation](#plugin-installation)
  - [Network Installation](#network-installation)
  - [Manual Installation](#manual-installation)
- [Plugins](#plugins)
  - [Remote Cracking](#remote_cracking)
    - [Server Configuration](#server-configuration)
      - [1) Generating certificates](#1-generating-certificates)
      - [2) Installing the server](#2-installing-the-server)
      - [3) Starting the server](#3-starting-the-server)
      - [4) Exposing your FTP server ports on your PC](#4-exposing-your-ftp-server-ports-on-your-pc)
      - [5) Exposing your FTP server ports on your router](#5-exposing-your-ftp-server-ports-on-your-router)
      - [6) Setting up Dynamic DNS](#6-setting-up-dynamic-dns)
      - [7) Testing it](#7-testing-it)
    - [Pwnagotchi Configuration](#pwnagotchi-configuration)
  - [iPhone GPS](#iphone_gps)
    - [iPhone Configuration](#iphone-configuration)
    - [Pwnagotchi Configuration](#pwnagotchi-configuration-1)
  - [Aftershake](#aftershake)
    - [Requirements](#requirements)
    - [Pwnagotchi Configuration](#pwnagotchi-configuration-2)
- [Credits](#credits)
- [License](#license)

---

<br>

# Installing the plugins

### Network installation
Add to `/etc/pwnagotchi/config.toml` :
```toml
main.custom_plugin_repos = [
 "https://github.com/evilsocket/pwnagotchi-plugins-contrib/archive/master.zip",
 "https://github.com/xentrify/custom-pwnagotchi-plugins/archive/master.zip"
]
```

Next, `sudo pwnagotchi plugins update` and `sudo pwnagotchi plugins install <plugin>`.

Now you should be able to continue with configuring the plugins using the next section.

### Manual installation
1. Download the the github files [here](https://github.com/xentrify/custom-pwnagotchi-plugins/archive/master.zip), or using git clone: `git clone https://github.com/xentrify/custom-pwnagotchi-plugins.git`.
2. Extract the files if needed and `cd` in the folder.
3. Copy the plugins of choice to the custom-plugin directory using `sudo cp <filename> /usr/local/share/pwnagotchi/custom-plugins/<filename>`.
Now you should be able to continue with configuring the plugins using the next section.

---

<br>

# Plugins

## Remote_Cracking

Allows you to set up your own FTP Server and pwnagotchi client that cracks your handshakes automatically. You can follow the guide to set it up.

## Server Configuration

### 1) Generating certificates

**Windows**

1. Download openssl [here](https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/openssl-for-windows/openssl-0.9.8k_X64.zip).
2. Extract the zip file and `cd` into it.
3. Run this command to generate the certificates:
`bin\openssl.exe req -new -x509 -days 365 -nodes -newkey rsa:2048 -out cert.pem -keyout key.pem`.

**Linux**
1. Install `openssl` and `libssl-dev` using `apt-get install openssl libssl-dev`.
2. Run this command to generate the certificates: `openssl req -new -x509 -days 365 -nodes -newkey rsa:2048 -out cert.pem -keyout key.pem`.

Create a directory named `remote_cracking` and copy the generated files `cert.pem` and `key.pem` to it.

### 2) Installing the server

**Windows**

1. Install `pyftpdlib` and `pyopenssl` using `python -m pip install pyftpdlib pyopenssl`. Also install 7-Zip [here](https://www.7-zip.org/a/7z2408-x64.exe).
2. Download the server script [here](https://github.com/xentrify/custom-pwnagotchi-plugins/blob/main/remote_cracking_server.py).
3. Download hashcat [here](https://github.com/hashcat/hashcat/releases/download/v6.2.3/hashcat-6.2.3.7z) and extract it using 7-Zip.
4. Move the whole hashcat directory and the server script into the `remote_cracking` directory (with the certificates).
5. Open the directory and create a folder named `wordlists` and one named `handshakes`.
6. Place in the wordlists you want to use to crack. For testing, you can download one [here](https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt).

**Linux**
1. Install `pyftpdlib` and `pyopenssl` using `python -m pip install pyftpdlib pyopenssl`.
2. Download the server script using `curl -O https://raw.githubusercontent.com/xentrify/custom-pwnagotchi-plugins/main/remote_cracking_server.py .`.
3. Download hashcat using `sudo apt-get install hashcat`
4. Move the server script into the directory using `mv remote_cracking_server.py remote_cracking`.
5. Open the directory using `cd remote_cracking`.
5. Create a handshake and wordlist directory using `mkdir wordlists handshakes`. 
6. Place in the wordlists you want to use to crack. For testing, you can use `curl -O https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt wordlists`.

### 3) Starting the server

**Windows**

1. If you followed the instructions and made every directory, you can use this command:

```python remote_cracking_server.py -d handshakes -c cert.pem -k key.pem -I hashcat-6.2.3/hashcat.exe -w wordlists -P yourpassword```

**Linux**
1. If you followed the instructions and made every directory, you can use this command:

```sudo python remote_cracking_server.py -d handshakes -c cert.pem -k key.pem -I /usr/bin/hashcat -w wordlists -P yourpassword```

**Options (only for customization)**
```commandline
usage: server.py [-h] [-i INTERVAL] [-p PORT] [-U USER] -P PASSWORD -d DIRECTORY -c CERT -k KEY -I INTERPRETER -w WORDLISTS

options:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        Interval between checking for new handshakes in seconds (default: 5)

Builtin FTP Server Settings:
  -p PORT, --port PORT  Port of the FTP server (default: port)
  -U USER, --user USER  Username of the FTP server (default: user)
  -P PASSWORD, --password PASSWORD
                        Password of the FTP server (required due to safety)
  -d DIRECTORY, --directory DIRECTORY
                        Directory of the FTP server
  -c CERT, --cert-file CERT
                        Path to the cert file (required)
  -k KEY, --key-file KEY
                        Path to the key file (required)

Cracking Settings:
  -I INTERPRETER, --interpreter INTERPRETER
                        Interpreter of hashcat (required)
  -w WORDLISTS, --wordlists WORDLISTS
                        Wordlist(s) used for cracking, can be one file or a directory (required)
```
### 4) Exposing your FTP server ports on your PC
**Windows**

1. Search for `Windows Defender` in your search bar and choose the option that ends in `Advanced Security`. 
2. Click on `Inbound Rules` and `New Rule`. 
3. Choose `Port` for type. 
4. Choose `TCP` and `Specific local ports`. 
5. Enter `49152-65534,8888` (Change this option if you've set a custom port).
6. `Allow the connection` and keep everything checked (Domain, Private and Public). 
7. Finally, give it a name.

**Linux**

Differs per distro. Alot of the times it is not needed.

### 5) Exposing your FTP server ports on your router

Next up is setting up port forwarding in your router. This will allow it to be accessible outside your network.
To get started, look up your router's IP address. On Windows, open command prompt and run `ipconfig`. Look for `Default Gateway`.
For Linux, try running `ip route show default`. Open the IP in your browser and log in. You can find the default login
online or on the back of your router. The next steps will only be the settings as configuring them will differ per router. 
Just search for your router's manual and read the instructions. You will first have to set a static IP for your PC. After
this, forward `8888` (or your custom port) and the port range `49152-65534`.

### 6) Setting up Dynamic DNS

Only continue if you have a dynamic IP.

**1. Claim hostname**

1. Go to [duckdns.org](https://duckdns.org) and sign in using any of the options listed at the top.
2. Claim a hostname by typing a subdomain in the input and pressing `add domain`.

**2. Set up the updater**

**Windows**

1. Install DuckSetup [here](https://github.com/CaptainDapper/DuckService/releases/download/v1.0/DuckService.zip).
2. Extract the ZIP file and run `DuckSetup.exe`.
3. Enter the hostname you claimed (only the part before .duckdns.org is required)
4. Enter the token located under your mail on the DuckDNS home page.
5. Set the interval to something between 1 and 5.
6. Press `Install Service`, wait until it's done and reboot.

**Linux**

1. Install docker using `curl -fsSL get.docker.com | bash`
2. Change the subdomain in the command to the hostname you claimed (only the part before .duckdns.org is required).
3. Change the token in the command to the one located under your mail on the DuckDNS home page.
4. Run the final command.
```commandline
docker run -d \
  --name=duckdns \
  -e SUBDOMAINS=<YOUR SUBDOMAIN> \
  -e TOKEN=<YOUR TOKEN> \
  --restart unless-stopped \
  lscr.io/linuxserver/duckdns:latest
```

**Other**

* [Home Assistant](https://www.home-assistant.io/integrations/duckdns/)
* [Other operating systems and routers](https://www.duckdns.org/install.jsp)

### 7) Testing it

Sometimes the FTP server is not accessible from the outside, you can use these tools to test it:
* **[FTPTest](https://ftptest.net/)**
* **[PortCheckTool](https://www.portchecktool.com/)**

### Pwnagotchi configuration

**Required:**

```toml
# INSTALLATION: https://github.com/PwnPeter/pwnagotchi-plugins#how-to-use
main.plugins.hashie-hcxpcapngtool.enabled = true
```

```toml
main.plugins.remote_cracking.enabled = true
main.plugins.remote_cracking.server = "123.456.789.123" # or somedomain.duckdns.org
main.plugins.remote_cracking.port = 8888
main.plugins.remote_cracking.user = "user"
main.plugins.remote_cracking.password = "Pwn4g0tchiL0L"
```
**Optional:**
```toml
main.plugins.remote_cracking.display_cracked = true # (default: true)
main.plugins.remote_cracking.potfile = "/root/remote_cracking.potfile" # (default: "/root/remote_cracking.potfile")
main.plugins.remote_cracking.orientation = "vertical" # (default: horizontal)
main.plugins.remote_cracking.position = "10,90"
```

---

<br>

## iPhone_GPS

Saves GPS coordinates whenever an handshake is captured. Uses your iPhone's GPS via website requests and Shortcuts.

### iPhone Configuration
1. Download [this shortcut](https://routinehub.co/shortcut/19128/)
2. Follow the instructions
3. Set up an automation to run it whenever your pwnagotchi connects via bluetooth.

For the location sending to work you will need a stable connection with your iPhone and pwnagotchi using bt-tether.
### Pwnagotchi Configuration
**Required:**
```toml
main.plugins.iphone_gps.enabled = true
```
**Optional:**
```toml
main.plugins.iphone_gps.use_last_loc = true # (default: false)
main.plugins.linespacing = 15 # (default: 10)
```

---

<br>

## Aftershake

A plugin that handles everything after a handshake. AircrackOnly, Hashie, Quickdic, etc. All in one.

### Requirements
* hcxpcapngtool (`sudo apt-get -y install hcxtools`) (if hashie is enabled)
* aircrack-ng (`sudo apt-get -y install aircrack-ng`)

### Pwnagotchi Configuration
**Required:**
```toml
main.plugins.gps.enabled = true # GPSD can also be used, same for my iphone_gps plugin.
main.plugins.gps.device = "/dev/ttyUSB0"
main.plugins.gps.speed = 19200

main.plugins.aftershake.enabled = true
```

**Optional:**
```toml
main.plugins.aftershake.wordlist_folder = "/root/custom_folder/" # (default: "/root/wordlist_folder/")
main.plugins.aftershake.hashie = false # (default: true)
main.plugins.aftershake.face = "(>.O)" # (default: "(◕.◕)")
main.plugins.aftershake.orientation = "vertical" # (default: horizontal)
```

---

<br>

# Credits
* [PwnPeter](https://github.com/PwnPeter) for the easy plugin configuration part.
* junohea.mail@gmail.com for the `hashie-hcxpcapngtool` plugin
* pwnagotchi@rossmarks.uk for the `quickdic` plugin
* evilsocket@gmail.com for the `aircrackonly` plugin
* @nagy_craig for the `display-password` plugin
* 33197631+dadav@users.noreply.github.com for the `wpa-sec` plugin

---

<br>

# License
This repository is licensed under the GPL 3 license.
