# AstroDiscovery

A portable, offline plate solving station for astrophotography. Upload a photo of the night sky and instantly determine the exact celestial coordinates, field of view, orientation, and plate scale — with no internet required.

## What is Plate Solving?

Plate solving analyzes star patterns in an astrophotography image and matches them against a star catalog to determine precisely where in the sky the image was taken. It reports:

- **Right Ascension / Declination** — the exact sky coordinates of the image center
- **Field of View** — the angular size of the image on the sky
- **Plate Scale** — arcseconds per pixel
- **Rotation** — orientation relative to celestial north

## Features

- **Dual solver engine** — runs both [Astrometry.net](https://astrometry.net) and [ASTAP](https://www.hnsky.org/astap.htm), with intelligent chaining (Astrometry.net solves first, then feeds coordinates to ASTAP for a fast confirmation)
- **Web UI** — dark red/black night-vision theme, drag-and-drop upload from any browser (iPhone, Android, laptop)
- **Camera integration** — browse and solve photos directly from a USB-connected DSLR via gphoto2
- **Object identification** — identifies Messier catalog objects (110 objects) within the solved field of view
- **Pointing error** — computes RA/Dec and Az/El nudge directions to a target (e.g., "Nudge LEFT 0.38 deg, Nudge UP 0.19 deg")
- **GPS location** — iPhone GPS button for Az/El calculations (requires HTTPS)
- **Offline** — all star catalogs are local. No internet required in the field
- **RAW support** — Nikon NEF, Canon CR2, Sony ARW auto-converted to FITS
- **Also accepts** FITS, JPG, TIFF, PNG
- **CLI tool** — `platesolve` command for scripting and batch processing
- **Portable** — runs as a Proxmox VM (exportable to VirtualBox) or on a Raspberry Pi Zero 2 W as a USB/WiFi appliance

## Quick Start

### Web UI
Open `https://<device-ip>` in any browser. Drag and drop an image. Results appear in seconds (VM) or ~90 seconds (Pi Zero).

### Camera Tab
Plug a Nikon D7200 (or other PTP-compatible camera) into the Pi via USB. Open the Camera tab in the web UI to browse and solve photos directly from the camera.

### Command Line
```bash
ssh root@starfinder
platesolve /root/photo.NEF --fov 4.55
```

### With Coordinate Hints (faster)
```bash
platesolve /root/photo.NEF --fov 4.55 --ra 6.5 --dec 5.0
```

## Deployment Platforms

### 1. Proxmox VM (StarFinder)
A Debian 12 virtual machine with everything pre-installed. Can be exported to VirtualBox for field use on a laptop.
- **Access:** `https://starfinder` or `https://10.1.10.196`
- **Solve time:** ~5-10 seconds

### 2. Raspberry Pi Zero 2 W (Deployed)
A $15 USB appliance that provides plate solving over WiFi hotspot or USB gadget mode.
- **WiFi:** Connect to SSID "AstroDiscovery" (password: stargazer), open `https://10.42.0.1`
- **USB:** Plug into laptop, Pi is at `10.42.1.1`
- **Camera:** Plug DSLR into Pi via USB hub, browse and solve from the Camera tab
- **Solve time:** ~80-100 seconds
- **HTTPS:** Self-signed cert enables GPS on iOS. Install profile via `https://<ip>/cert`

## Documentation

- **[AstroDiscovery_Manual.md](AstroDiscovery_Manual.md)** — Complete user manual (VM + Pi Zero usage, tips, troubleshooting)
- **[PiZero_PlateServer.md](PiZero_PlateServer.md)** — Raspberry Pi Zero appliance technical reference
- **[NOTES.md](NOTES.md)** — Development log

## Architecture

```
           Browser / iPhone
                |
          Web UI (Flask, HTTPS port 443)
           /         |          \
     Upload tab   Camera tab   Pointing Error
          |          |          (Messier catalog +
     platesolve   gphoto2       astropy Az/El)
      /       \      |
Astrometry   ASTAP   USB PTP
(Tycho-2)   (D50)   (Nikon D7200)
      \       /
   JSON results + WCS
```

## Star Databases

| Database | Size | Coverage |
|----------|------|----------|
| Tycho-2 (scales 7-19) | 285 MB | ~22 arcmin to ~33 deg, full sky |
| ASTAP D50 | 935 MB | ~0.2 to ~6 deg, full sky |

## Supported Cameras

Any camera that produces NEF, CR2, ARW, FITS, JPG, TIFF, or PNG files. Camera tab requires PTP/USB support (2700+ models via gphoto2). Tested with:
- Nikon D7200 (APS-C) with 200mm-500mm lenses

## Requirements

| Platform | CPU | RAM | Disk |
|----------|-----|-----|------|
| VM (StarFinder) | 2 cores | 4 GB | 32 GB |
| Pi Zero 2 W | Quad Cortex-A53 | 416 MB | 29 GB SD |

## License

This project uses open-source plate solving engines:
- [Astrometry.net](https://astrometry.net) — BSD/GPL licensed
- [ASTAP](https://www.hnsky.org/astap.htm) — Mozilla Public License 2.0
