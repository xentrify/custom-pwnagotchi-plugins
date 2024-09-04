# Custom Pwnagotchi Plugins
This repository contains all of my custom-made pwnagotchi plugins (the ones that were finished). You can set them up using the following guide(s) or if you know what to do, the setup is also included in each file. If you found any bugs or have an issue, you can report them [here](https://github.com/xentrify/custom-pwnagotchi-plugins/issues/new/choose) or on [reddit](https://reddit.com/u/xentrifydev). Also reach out to me if you have any suggestions or ideas for new plugins, I would love to hear them!
# Todo
- [X] Release a new plugin! ([Thread](https://discord.com/channels/717817147853766687/1278003598416019518))
- [x] Update README.md on how to setup Duck DNS
- [ ] Rewrite iPhone_GPS using [GPS_more](https://github.com/Sniffleupagus/pwnagotchi_plugins/blob/main/gps_more.py)
- [ ] Fix package checking (aftershake)

# Installation
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

# Plugins

## Remote_Cracking
Allows you to set up your own FTP Server and pwnagotchi client that cracks your handshakes automatically. You can follow the guide to set it up.

### Server Configuration 1 (Generating certificates)
For the FTP server to work, you'll need to generate certificates so you can send data encrypted. To generate certificates, you need to install openssl:

**Windows**

1. Download openssl [here](https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/openssl-for-windows/openssl-0.9.8k_X64.zip).
2. Extract the zip file and `cd` into it in a new command prompt window.
3. Run this command to generate the certificates:
`bin\openssl.exe req -new -x509 -days 365 -nodes -newkey rsa:2048 -out cert.pem -keyout key.pem`. If it gives errors about the config missing, add this option: `-config openssl.cnf` 

**Linux**
1. Install openssl using `apt-get install openssl`.
2. Run this command to generate the certificates:
3. `openssl req -new -x509 -days 365 -nodes -newkey rsa:2048 -out cert.pem -keyout key.pem`. If you get errors, try installing libssl-dev: `apt-get install libssl-dev`. If that doesn't work, search for solutions online.

Save the generated files (cert.pem, key.pem) somewhere as you will need to point to them when you run the server script.

### Server Configuration 2 (The Script)
The server script is compatible with both Linux and Windows (MacOS should also work). You can download it from [here](https://example.com), and these are the options:
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
This is pretty self-explanatory. Get it running before continuing.

### Server Configuration 3 (Exposing your FTP port)
**Windows**

Search for `Windows Defender` in your search bar and choose the option that ends in `Advanced Security`. 
Click on `Inbound Rules` and `New Rule`. Choose `Port` for type. Choose `TCP` and `Specific local ports`. Enter `49152-65534,<the port you've set in server.py>`.
`Allow the connection` and keep everything checked (Domain, Private and Public). Finally, give it a name.

For Linux, I didn't have to open ports in my firewall. This can be different for you, just search online if you get errors or if it's not working.

**Router (Port forwarding)**

Next up is setting up port forwarding in your router. This will allow it to be accessible outside your network.
To get started, look up your router's IP address. On Windows, open command prompt and run `ipconfig`. Look for `Default Gateway`.
For Linux, try running `ip route show default`. Open the IP in your browser and log in. You can find the default login
online or on the back of your router. The next steps will only be the settings as configuring them will differ per router. 
Just search for your router's manual and read the instructions. You will first have to set a static IP for your PC. After
this, forward your custom port and the port range `49152-65534`.

### Server Configuration 4 (Dynamic DNS)

Most routers will have a dynamic IP. If you don't, you can skip this step. If you do, this means that the IP can change over time. 
To have a static endpoint, so your pwnagotchi can always reach you, you will have to use a dynamic DNS. There are alot of free
services that provide this. [Duck DNS](https://www.duckdns.org/) is a great one and will be used in this example. 

**Duck DNS (Signup)**

Go to [duckdns.org](https://duckdns.org) and sign in using any of the options listed at the top. 
When you have signed in, claim a domain by typing a subdomain in the input and pressing "add domain".
When done correctly, the page should reload and you should see your domain listed next to your public IP (which was set automatically)

Next up is configuring an updater, which updates the domain so it'll always point to the right IP.

**Windows**

In my testing, the best DuckDNS updater that works with Windows is DuckService. Download the zip [here](https://github.com/CaptainDapper/DuckService/releases/download/v1.0/DuckService.zip).
To set it up, extract the ZIP file and simply run `DuckSetup.exe`. 
In the window that pops up, enter the domain you've claimed (only the subdomain part is needed).
Next, enter the token from your DuckDNS account. It's located under your mail on the homepage.
Finally, set the interval to your liking (or keep the default) and press "Install Service". 
After it has completed the installation, just reboot!

**Linux**

For Linux, we are going to set up a docker container. If you do not have docker installed, you can follow the instructions [here](https://docs.docker.com/get-started/get-docker/).
To start your container, run this command, changing the options:
```commandline
docker run -d \
  --name=duckdns \
  -e SUBDOMAINS=<YOUR SUBDOMAIN> \
  -e TOKEN=<YOUR TOKEN>> \
  --restart unless-stopped \
  lscr.io/linuxserver/duckdns:latest
```

You can also integrate DuckDNS in [home assistant](https://www.home-assistant.io/integrations/duckdns/) or for more advanced users, setup a VPN tunnel.

**Testing it**

Sometimes the FTP server is not accessible from the outside, you can use these tools to test it:
* **[FTPTest](https://ftptest.net/)**
* **[PortCheckTool](https://www.portchecktool.com/)**
### Pwnagotchi configuration
**Required:**
```toml
# INSTALL: https://raw.githubusercontent.com/PwnPeter/pwnagotchi-plugins/master/hashie-hcxpcapngtool.py
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
> [!NOTE]
> For now, only '.22000' (WPA handshakes) will be cracked, PMKID (.16800) support will be added later!

## iPhone_GPS
Saves GPS coordinates whenever an handshake is captured. Uses your iPhone's GPS via website requests and Shortcuts.
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
### Phone Configuration (required!)
Set up this [this shortcut](https://routinehub.co/shortcut/19128/) to send the GPS from your iPhone. Optionally, you can make it run whenever the pwnagotchi connects via bluetooth.

For the location sending to work you will need a stable connection with your iPhone and pwnagotchi using bt-tether.


## Aftershake
A plugin that handles everything after a handshake. AircrackOnly, Hashie, Quickdic, etc. All in one.
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
> [!NOTE]
> ~~Don't forgot to enable hashie if you want your handshakes to be converted!~~ Hashie is now enabled by default! Make sure to download the required packages.
### Package Requirements
* hcxpcapngtool (`sudo apt-get -y install hcxtools`) (if hashie is enabled)
* aircrack-ng (`sudo apt-get -y install aircrack-ng`)
> [!NOTE]
> Try running `sudo run apt-get update` if you run into issues. Do NOT run `sudo apt-get upgrade` as this can break your pwnagotchi installation.


# Credits
* [PwnPeter](https://github.com/PwnPeter) for the easy plugin configuration part.
* junohea.mail@gmail.com for the `hashie-hcxpcapngtool` plugin
* pwnagotchi@rossmarks.uk for the `quickdic` plugin
* evilsocket@gmail.com for the `aircrackonly` plugin
* @nagy_craig for the `display-password` plugin

# License
This repository is licensed under the GPL 3 license.
