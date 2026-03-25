# AstroDiscovery Pi Zero - USB Plate Solving Appliance

> **Status:** Concept / Future Build
> **Date:** March 2026

---

## Concept

A Raspberry Pi Zero 2 W configured as a **multi-mode plate solving appliance**:

1. **USB Mode** — Plug into a laptop via USB cable. Pi appears as a network device. SSH in and solve.
2. **WiFi Hotspot Mode** — Pi broadcasts a WiFi network. Connect from iPhone/phone/laptop, open a web browser, drag-and-drop images to solve.
3. **Camera Direct Mode** — Connect your DSLR to the Pi via USB. Browse, download, and solve photos directly from the camera through the web UI on your phone. No intermediary app needed.

**No internet required. No app to install. No Nikon WMU needed.**

---

## Hardware

| Component | Details | Cost |
|-----------|---------|------|
| Raspberry Pi Zero 2 W | Quad-core Cortex-A53 @ 1 GHz, 512 MB RAM, WiFi, USB OTG | ~$15 |
| MicroSD Card (32 GB) | SanDisk Extreme or similar A2-rated | ~$8 |
| USB OTG Hub/Adapter | Micro-USB OTG to USB-A (for camera + power) | ~$5 |
| USB Cable (power) | Micro-USB to USB-A/C, data-capable | ~$2 |
| Camera USB Cable | USB-A to Micro-B (Nikon D7200) or appropriate for camera | ~$3 |
| Case | 3D-printed or off-the-shelf Pi Zero case | optional |
| **Total BOM** | | **~$33** |

> **Note on USB OTG:** The Pi Zero 2 W has a single micro-USB data port. To connect a camera AND receive power, you need a USB OTG hub/adapter with external power input, or power the Pi via the GPIO header pins from a battery/regulator instead of USB.

### Storage Budget (32 GB card)
| Item | Size |
|------|------|
| Raspberry Pi OS Lite | ~2 GB |
| Astrometry.net + Tycho-2 indexes | 285 MB |
| ASTAP CLI + D50 database | ~1 GB |
| Python, Flask, libraries | ~500 MB |
| Working space for images | ~28 GB |

---

## USB Gadget Mode

The Pi Zero's micro-USB port supports OTG gadget mode — it appears as a USB Ethernet adapter when plugged into a laptop. Power and networking over a single cable.

### Configuration

**`/boot/config.txt`** — add at the end:
```
dtoverlay=dwc2
```

**`/boot/cmdline.txt`** — append after `rootwait`:
```
modules-load=dwc2,g_ether
```

**`/etc/network/interfaces.d/usb0`**:
```
auto usb0
iface usb0 inet static
    address 10.42.0.2
    netmask 255.255.255.0
```

### Usage
1. Plug Pi into laptop USB port (powers on automatically)
2. Wait ~15 seconds for boot
3. SSH in: `ssh root@10.42.0.2`
4. Solve: `platesolve /tmp/photo.NEF --fov 4.55`

> **Note:** On Windows, the Pi appears as a RNDIS Ethernet device. No drivers needed on Windows 10/11, macOS, or Linux.

---

## WiFi Hotspot Mode

The Pi broadcasts its own WiFi network for phone/tablet access. Connect and use the web UI — no internet needed.

### Components
- **`hostapd`** — creates the WiFi access point ("AstroDiscovery")
- **`dnsmasq`** — DHCP server for connected clients
- **Flask web server** — serves the plate solving UI on port 80

### Configuration

**`/etc/hostapd/hostapd.conf`**:
```
interface=wlan0
driver=nl80211
ssid=AstroDiscovery
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=starfinder
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

**`/etc/dnsmasq.conf`**:
```
interface=wlan0
dhcp-range=10.42.1.10,10.42.1.50,255.255.255.0,24h
address=/#/10.42.1.1
```

**`/etc/network/interfaces.d/wlan0`**:
```
auto wlan0
iface wlan0 inet static
    address 10.42.1.1
    netmask 255.255.255.0
```

### Usage
1. Pi powers up (USB battery or laptop)
2. iPhone/phone connects to WiFi network **"AstroDiscovery"** (password: `starfinder`)
3. Open Safari/Chrome: **http://10.42.1.1**
4. Drag/drop or tap to upload photo
5. Results appear in ~15-30 seconds

> The `dnsmasq` captive portal config (`address=/#/...`) redirects all DNS queries to the Pi, so any URL typed in the browser goes to AstroDiscovery.

---

## Camera Direct Mode

Connect your DSLR directly to the Pi via USB and control it from your phone's browser. No camera WiFi, no manufacturer app, no file transfers between devices.

### How It Works

```
DSLR Camera ----USB cable----> Pi Zero <~~~~WiFi~~~~> iPhone
  (PTP/USB)                  (gphoto2)   (hostapd)    (Safari)
                              (Flask)
```

1. Camera connects to Pi via USB (PTP — Picture Transfer Protocol)
2. Pi runs `gphoto2` to communicate with the camera
3. Pi broadcasts WiFi hotspot
4. iPhone connects to WiFi, opens web UI
5. Web UI shows a **Camera** tab with thumbnails from the camera
6. Tap a photo to download it to the Pi and plate solve it instantly

### Supported Cameras

`gphoto2` supports **2700+ camera models** via PTP/USB, including:

| Manufacturer | Example Models |
|---|---|
| **Nikon** | D7200, D7500, D500, D780, D850, Z5, Z6, Z7, Z8, Z9 |
| **Canon** | EOS R, R5, R6, 5D series, 6D series, 90D, Rebel series |
| **Sony** | A7 series, A6000 series, A9 series |
| **Others** | Fujifilm, Olympus, Pentax, Panasonic |

Full list: `gphoto2 --list-cameras`

### Software Components

- **`gphoto2`** — command-line camera control (`apt install gphoto2`)
- **`libgphoto2`** — underlying PTP library (installed as dependency)
- **Flask camera routes** — new endpoints in the web app

### gphoto2 Key Commands

```bash
# Detect connected camera:
gphoto2 --auto-detect

# List files on camera:
gphoto2 --list-files

# Download a specific file:
gphoto2 --get-file 42 --filename /tmp/photo.NEF

# Download all files:
gphoto2 --get-all-files

# Get thumbnail for a file:
gphoto2 --get-thumbnail 42

# Camera info:
gphoto2 --summary
```

### Web UI Camera Tab

The web UI gains a **Camera** tab alongside the existing Upload tab:

| Feature | Description |
|---|---|
| **Camera status** | Shows connected camera model, battery level, image count |
| **Thumbnail grid** | Scrollable grid of photo thumbnails from the camera |
| **Tap to solve** | Tap any thumbnail to download the full image and solve it |
| **Batch select** | Select multiple images for batch solving |
| **Auto-detect** | Camera connection detected automatically on USB plug-in |

### Architecture with Camera

```
iPhone Safari                     Pi Zero
  |                                 |
  |---WiFi--> Flask (port 80)       |
  |             |                   |
  |         /camera/list -----> gphoto2 --list-files
  |         /camera/thumb/42 -> gphoto2 --get-thumbnail 42
  |         /camera/solve/42 -> gphoto2 --get-file 42
  |                               |
  |                           platesolve
  |                            /       \
  |                    Astrometry    ASTAP
  |                            \       /
  |         <-- JSON results <-- solve complete
```

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/camera/status` | GET | Camera model, battery, file count |
| `/camera/list` | GET | List all files with metadata |
| `/camera/thumbnail/<n>` | GET | JPEG thumbnail for file n |
| `/camera/solve/<n>` | POST | Download file n and plate solve it |
| `/camera/solve-batch` | POST | Solve multiple selected files |

### Power Considerations

The Pi Zero's single micro-USB port is used for power in gadget mode. To connect a camera via USB, you need one of:

1. **USB OTG hub with power input** — a small hub that accepts external power while providing a USB-A port for the camera (~$5)
2. **GPIO power** — power the Pi via the 5V/GND GPIO pins from a USB battery pack with bare wires or a GPIO power adapter, leaving the micro-USB port free for the camera via OTG adapter
3. **Powered USB hub** — a small hub that powers both the Pi and provides a port for the camera

Option 2 (GPIO power) is the most compact for field use.

### Field Workflow: Camera Direct Mode

```
1. Power on Pi (battery pack to GPIO or powered hub)
2. Plug camera USB into Pi's OTG port
3. Connect iPhone to "AstroDiscovery" WiFi
4. Open Safari: http://10.42.1.1
5. Tap "Camera" tab
6. Browse thumbnails, tap to solve
7. Results appear in ~15-30 seconds
```

**No WiFi switching. No WMU app. No file juggling. Just tap and solve.**

---

## Web UI

A mobile-first, dark-themed web interface designed for astronomers in the field at night.

### Features
- **Drag-and-drop file upload** (or tap to select on mobile)
- **Night vision theme** — dark red/black color scheme to preserve dark adaptation
- **Large touch targets** — designed for cold fingers and phone screens
- **Optional FOV/RA/Dec inputs** — with sensible defaults
- **Dual solver results** — shows both Astrometry.net and ASTAP
- **Raw output toggle** — view full solver logs if needed
- **No app install** — works in any browser (Safari, Chrome, Firefox)

### Supported Uploads
NEF, CR2, ARW, FITS, JPG, TIFF, PNG — up to 100 MB per file.

### Architecture
```
iPhone/Phone                    Pi Zero
  Safari ----WiFi----> Flask (port 80)
                           |
                           v
                       platesolve script
                        /            \
               Astrometry.net      ASTAP
                        \            /
                         v          v
                       JSON response
                           |
                           v
                       Results page
```

---

## Software Stack

Identical to the StarFinder VM — the `platesolve` script is unchanged.

| Software | Notes |
|----------|-------|
| Astrometry.net 0.93 | `apt install astrometry.net astrometry-data-tycho2` |
| ASTAP CLI | ARM64 build from SourceForge |
| D50 star database | `dpkg -i d50_star_database.deb` |
| dcraw | `apt install dcraw` |
| gphoto2 | `apt install gphoto2` — camera control via PTP/USB |
| Python 3 + Astropy + Pillow | `apt install python3-astropy python3-pil` |
| Flask | `apt install python3-flask` |
| hostapd + dnsmasq | `apt install hostapd dnsmasq` |
| platesolve script | `/usr/local/bin/platesolve` (copied from VM) |

---

## Performance Estimates

| Operation | Pi Zero 2 W | StarFinder VM |
|-----------|-------------|---------------|
| Star extraction | ~5-10 sec | ~1 sec |
| Solve with hints | ~10-30 sec | ~1-5 sec |
| ASTAP with hints | ~2-5 sec | ~1-2 sec |
| Blind solve | ~2-10 min | ~10-30 sec |
| RAW conversion | ~10-15 sec | ~2 sec |

### RAM Mitigation (512 MB)
- Downsample images aggressively (`--downsample 4`)
- Use ASTAP preferentially (lower memory footprint)
- Use `zram` compressed swap instead of SD card swap
- Convert NEF to smaller FITS before solving

### Alternative Hardware
If 512 MB proves too tight:

| Board | RAM | USB OTG | WiFi | Price |
|-------|-----|---------|------|-------|
| Pi Zero 2 W | 512 MB | Yes | Yes | ~$15 |
| Orange Pi Zero 2W | 1 GB | Yes | Yes | ~$20 |
| Pi 3A+ | 512 MB | No | Yes | ~$25 |
| Pi 4 | 1-8 GB | No* | Yes | ~$35+ |

*Pi 4 lacks USB gadget mode but works great as a WiFi-only appliance.

---

## Workflow Summary

### Mode 1: USB Cable (laptop)
```
Laptop USB port --cable--> Pi Zero
  ssh root@10.42.0.2
  scp photo.NEF root@10.42.0.2:/tmp/
  platesolve /tmp/photo.NEF --fov 4.55
```

### Mode 2: WiFi Hotspot (phone/tablet)
```
Phone connects to WiFi "AstroDiscovery"
  Open http://10.42.1.1
  Upload photo via web UI
  View results in browser
```

### Mode 3: Camera Direct (phone + camera)
```
Camera ---USB---> Pi Zero ~~~WiFi~~~> iPhone
                  (gphoto2)           (Safari web UI)
  Power via GPIO pins or powered USB hub
  Browse thumbnails, tap to solve
```

### Mode 4: All Simultaneously
USB gadget mode, WiFi hotspot, and camera connection can run at the same time — laptop users SSH while phone users browse camera and solve via the web UI.

---

## Optional Enhancements

| Enhancement | Description |
|-------------|-------------|
| **Read-only rootfs** | OverlayFS so Pi can be safely unplugged without corruption |
| **LED status** | GPIO-driven LED: off = idle, blinking = solving, solid = solved |
| **Auto-solve** | `inotifywait` watches upload directory, solves on arrival |
| **mDNS** | `avahi-daemon` so clients find it as `astrodiscovery.local` |
| **Battery** | LiPo + Adafruit PowerBoost for fully wireless operation |
| **Captive portal** | Auto-redirect to web UI when phone joins WiFi |
| **Result history** | SQLite log of all solves with timestamps |
| **Live capture** | Trigger camera shutter from web UI via `gphoto2 --capture-image-and-download`, then auto-solve |
| **Camera live view** | Stream camera live view to web UI for framing (gphoto2 supports this on many Nikon/Canon bodies) |

---

## Build Steps

1. Flash **Raspberry Pi OS Lite 64-bit** to SD card
2. Configure USB gadget mode (`dwc2` + `g_ether`)
3. Configure WiFi hotspot (`hostapd` + `dnsmasq`)
4. Enable SSH, set root password
5. Boot, connect via USB
6. Install packages:
   ```bash
   apt update && apt install -y \
     astrometry.net astrometry-data-tycho2 \
     dcraw gphoto2 python3-astropy python3-pil python3-flask \
     hostapd dnsmasq bc
   ```
7. Download and install ASTAP CLI (ARM64) + D50 database
8. Install `platesolve` script and web app
9. Test with sample images
10. Configure read-only filesystem (optional)
11. **Image the SD card** as a backup/master copy

---

## Comparison: VM vs Pi Zero

| | StarFinder VM | Pi Zero Appliance |
|---|---|---|
| **Host required** | Proxmox or VirtualBox | None (standalone USB device) |
| **Setup complexity** | Medium | Low (flash SD card) |
| **Solve speed** | ~1-5 sec | ~5-30 sec |
| **RAM** | 4 GB | 512 MB |
| **Portability** | Export VDI file | Carry the Pi (~10 grams) |
| **Power** | Host-dependent | USB bus power (~2.5W) |
| **Cost** | Free (uses existing server) | ~$25 |
| **Phone access** | No (SSH only) | Yes (WiFi + Web UI) |
| **Camera direct** | No | Yes (gphoto2 via USB) |
| **Field convenience** | Good | Excellent |

---

*AstroDiscovery — https://github.com/CodeSchnitzel/astro-discovery*
