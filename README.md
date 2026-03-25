# astro-discovery

A portable, offline plate solving station for astrophotography. Upload a photo of the night sky and instantly determine the exact celestial coordinates, field of view, orientation, and plate scale.

## What is Plate Solving?

Plate solving analyzes star patterns in an astrophotography image and matches them against a star catalog to determine precisely where in the sky the image was taken. It reports:

- **Right Ascension / Declination** — the exact sky coordinates of the image center
- **Field of View** — the angular size of the image on the sky
- **Plate Scale** — arcseconds per pixel
- **Rotation** — orientation relative to celestial north

## Features

- **Dual solver engine** — runs both [Astrometry.net](https://astrometry.net) and [ASTAP](https://www.hnsky.org/astap.htm), with intelligent chaining (Astrometry.net solves first, then feeds coordinates to ASTAP for a fast confirmation)
- **Web UI** — dark red/black night-vision theme, drag-and-drop upload from any browser (iPhone, Android, laptop)
- **Offline** — all star catalogs are local. No internet required in the field
- **RAW support** — Nikon NEF, Canon CR2, Sony ARW auto-converted to FITS
- **Also accepts** FITS, JPG, TIFF, PNG
- **CLI tool** — `platesolve` command for scripting and batch processing
- **Portable** — runs as a Proxmox VM (exportable to VirtualBox) or on a Raspberry Pi Zero as a USB/WiFi appliance

## Quick Start

### Web UI
Open `http://<starfinder-ip>` in any browser. Drag and drop an image. Results appear in seconds.

### Command Line
```bash
ssh root@starfinder
platesolve /root/photo.NEF --fov 4.55
```

### With Coordinate Hints (faster)
```bash
platesolve /root/photo.NEF --fov 4.55 --ra 6.5 --dec 5.0
```

## Deployment Options

### 1. Proxmox VM
A Debian 12 virtual machine with everything pre-installed. Can be exported to VirtualBox for field use on a laptop.

### 2. Raspberry Pi Zero (planned)
A $25 USB appliance that provides plate solving over a single USB cable or WiFi hotspot. Connect from your phone and solve directly from the browser.

See [PiZero_PlateServer_Design.md](PiZero_PlateServer_Design.md) for the full design.

## Documentation

- **[StarFinder_Manual.md](StarFinder_Manual.md)** — Complete user manual (connecting, usage, tips, VirtualBox export, troubleshooting)
- **[PiZero_PlateServer_Design.md](PiZero_PlateServer_Design.md)** — Raspberry Pi Zero appliance design document

## Architecture

```
           Browser / iPhone
                |
            Web UI (Flask, port 80)
                |
          platesolve script
           /            \
  Astrometry.net       ASTAP
  (Tycho-2 indexes)   (D50 database)
           \            /
        JSON results + WCS
```

## Star Databases

| Database | Size | Coverage |
|----------|------|----------|
| Tycho-2 (scales 7-19) | 285 MB | ~22 arcmin to ~33 deg, full sky |
| ASTAP D50 | 935 MB | ~0.2 to ~6 deg, full sky |

## Supported Cameras

Any camera that produces NEF, CR2, ARW, FITS, JPG, TIFF, or PNG files. Tested with:
- Nikon D7200 (APS-C) with 200mm-500mm lenses

## Requirements

- Debian 12+ (VM or Pi)
- 2 CPU cores, 4 GB RAM (VM) or 512 MB (Pi Zero)
- ~2 GB disk for OS + databases

## License

This project uses open-source plate solving engines:
- [Astrometry.net](https://astrometry.net) — BSD/GPL licensed
- [ASTAP](https://www.hnsky.org/astap.htm) — Mozilla Public License 2.0
