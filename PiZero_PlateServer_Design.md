# StarFinder Pi Zero - USB Plate Solving Appliance

> **Status:** Concept / Future Build
> **Date:** March 2026

---

## Concept

A Raspberry Pi Zero 2 W configured as a **dual-mode plate solving appliance**:

1. **USB Mode** — Plug into a laptop via USB cable. Pi appears as a network device. SSH in and solve.
2. **WiFi Hotspot Mode** — Pi broadcasts a WiFi network. Connect from iPhone/phone/laptop, open a web browser, drag-and-drop images to solve.

**No internet required. No app to install. One cable or zero cables.**

---

## Hardware

| Component | Details | Cost |
|-----------|---------|------|
| Raspberry Pi Zero 2 W | Quad-core Cortex-A53 @ 1 GHz, 512 MB RAM, WiFi, USB OTG | ~$15 |
| MicroSD Card (32 GB) | SanDisk Extreme or similar A2-rated | ~$8 |
| USB Cable | Micro-USB to USB-A/C, data-capable | ~$2 |
| Case | 3D-printed or off-the-shelf Pi Zero case | optional |
| **Total BOM** | | **~$25** |

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
- **`hostapd`** — creates the WiFi access point ("StarFinder")
- **`dnsmasq`** — DHCP server for connected clients
- **Flask web server** — serves the plate solving UI on port 80

### Configuration

**`/etc/hostapd/hostapd.conf`**:
```
interface=wlan0
driver=nl80211
ssid=StarFinder
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
2. iPhone/phone connects to WiFi network **"StarFinder"** (password: `starfinder`)
3. Open Safari/Chrome: **http://10.42.1.1**
4. Drag/drop or tap to upload photo
5. Results appear in ~15-30 seconds

> The `dnsmasq` captive portal config (`address=/#/...`) redirects all DNS queries to the Pi, so any URL typed in the browser goes to StarFinder.

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
Phone connects to WiFi "StarFinder"
  Open http://10.42.1.1
  Upload photo via web UI
  View results in browser
```

### Mode 3: Both Simultaneously
USB gadget mode and WiFi hotspot can run at the same time — laptop users SSH while phone users access the web UI.

---

## Optional Enhancements

| Enhancement | Description |
|-------------|-------------|
| **Read-only rootfs** | OverlayFS so Pi can be safely unplugged without corruption |
| **LED status** | GPIO-driven LED: off = idle, blinking = solving, solid = solved |
| **Auto-solve** | `inotifywait` watches upload directory, solves on arrival |
| **mDNS** | `avahi-daemon` so clients find it as `starfinder.local` |
| **Battery** | LiPo + Adafruit PowerBoost for fully wireless operation |
| **Captive portal** | Auto-redirect to web UI when phone joins WiFi |
| **Result history** | SQLite log of all solves with timestamps |

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
     dcraw python3-astropy python3-pil python3-flask \
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
| **Field convenience** | Good | Excellent |

---

*StarFinder project — Part of [Star-Trkr](../)*
