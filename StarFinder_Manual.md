# StarFinder Plate Solving Station - User Manual

> **VM:** StarFinder (Proxmox VMID 103)
> **OS:** Debian 12.12 (Bookworm)
> **IP:** DHCP (currently `10.1.10.196`)

---

## 1. Connecting to StarFinder

### SSH (recommended)
```bash
ssh root@starfinder
```
If DNS doesn't resolve, use the IP directly:
```bash
ssh root@10.1.10.196
```

### Web UI (plate solving from a browser)
Open **http://starfinder** or **http://10.1.10.196** in any browser. Drag and drop an image to solve it — no SSH needed.

### Proxmox Console
1. Open https://deepthought:8006
2. Click **VM 103 (StarFinder)** in the sidebar
3. Click **Console**

---

## 2. Getting Images Onto StarFinder

### Option A: Web UI Upload
The easiest method — just drag and drop files in the browser at `http://starfinder`.

### Option B: SCP from Windows
```powershell
scp C:\Photos\D72_53010.NEF root@starfinder:/root/
scp C:\Photos\*.NEF root@starfinder:/root/
```

### Option C: SCP from DeepThought
Run this **on StarFinder** after SSH-ing in:
```bash
scp root@deepthought:/path/to/files/*.NEF /root/
```

### Option D: VirtualBox Shared Folders (field use)
See [Section 7: VirtualBox Export](#7-taking-starfinder-into-the-field-virtualbox).

---

## 3. The `platesolve` Command

### Basic Usage
```bash
platesolve <image_file>
```
Runs **both** solvers (Astrometry.net and ASTAP) and reports results from each. Automatically converts RAW files to FITS.

### Examples

| Command | Description |
|---------|-------------|
| `platesolve /root/D72_53010.NEF` | Default FOV (4.55 deg) |
| `platesolve /root/image.NEF --fov 2.25` | Custom field of view |
| `platesolve /root/image.NEF --ra 6.5 --dec 5.0` | With coordinate hint (faster) |
| `platesolve /root/image.fits --fov 3.0` | FITS input |
| `platesolve /root/photo.jpg --fov 4.55` | JPG input |

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--fov <degrees>` | Field of view width in degrees | `4.55` (D7200 + 300mm) |
| `--ra <hours>` | Approximate RA in decimal hours (e.g. `6.5` = 06h 30m) | *(none)* |
| `--dec <degrees>` | Approximate Dec in decimal degrees (e.g. `-15.5`) | *(none)* |

### Supported Formats

| Format | Handling |
|--------|----------|
| `.NEF` `.CR2` `.ARW` | RAW — auto-converted to FITS |
| `.FITS` `.FIT` | Native — no conversion needed |
| `.JPG` `.TIFF` `.PNG` | Passed directly to solvers |

### Batch Solving
```bash
# Solve all NEF files:
for f in /root/*.NEF; do echo "=== $f ==="; platesolve "$f"; done

# Save results to a log file:
for f in /root/*.NEF; do platesolve "$f"; done > results.txt 2>&1
```

---

## 4. Understanding the Output

### Successful Solve
```
[+] SOLVED!
  Center RA:  06h 33m 27.46s       # Right Ascension of image center
  Center Dec: +05d 32m 18.61s      # Declination of image center
  Scale: 2.74 arcsec/pix           # Plate scale
  FOV: 4.58 x 3.06 deg            # Actual field of view
```

### Key Terms

| Term | Meaning |
|------|---------|
| **RA** (Right Ascension) | East-west position on the sky, like longitude (0h to 24h) |
| **Dec** (Declination) | North-south position on the sky, like latitude (-90 to +90 deg) |
| **Scale** | How many arcseconds each pixel covers |
| **FOV** | Total angular size of the image on the sky |

### Output Files
Each solve creates files alongside your image:

| File | Contents |
|------|----------|
| `image.wcs` | WCS solution (Astrometry.net) |
| `image.solved` | Marker indicating success |
| `image.ini` | ASTAP solution |
| `image.fits` | FITS conversion (if input was RAW) |

---

## 5. Tips for Best Results

### 1. Always Provide the FOV
If you change lenses or cameras, update `--fov`. This dramatically narrows the search.

| Camera + Lens | Approx FOV |
|---------------|------------|
| D7200 + 300mm | 4.55 deg |
| D7200 + 200mm | 6.75 deg |
| D7200 + 500mm | 2.70 deg |
| D7200 + 50mm | 26.5 deg |
| Full-frame + 300mm | 6.85 deg |
| Full-frame + 200mm | 10.3 deg |

**Formula:** `FOV = 2 * atan(sensor_width / (2 * focal_length)) * 180/pi`
D7200 sensor width = 23.5mm

### 2. Provide Coordinate Hints
If you know roughly where you pointed (even within 10 degrees), use `--ra` and `--dec`:
```bash
platesolve image.NEF --ra 5.5 --dec -1
```
This speeds solving from **minutes to seconds**.

### 3. Expose Properly
At least 20-30 stars should be visible. Underexposed images are harder to solve.

### 4. Avoid Heavy Star Trails
Short exposures (< 30 sec untracked) work best.

### 5. RAW is Better Than JPG
NEF files preserve faint stars that JPG compression discards.

---

## 6. Running the Solvers Individually

### Astrometry.net (`solve-field`)

```bash
# Blind solve (searches entire sky):
solve-field --no-plots --downsample 2 image.fits

# With scale hint:
solve-field --no-plots --downsample 2 \
  --scale-units degwidth --scale-low 3 --scale-high 6 image.fits

# With position hint (fastest):
solve-field --no-plots --downsample 2 \
  --scale-units degwidth --scale-low 3 --scale-high 6 \
  --ra 98.5 --dec 5.5 --radius 10 image.fits
```

Key flags: `--downsample N`, `--cpulimit N`, `--scale-low/high`, `--ra/--dec/--radius`

### ASTAP (`astap_cli`)

```bash
# Blind solve:
/opt/astap_cli/astap_cli -f image.fits -fov 4.55 \
  -D d50 -d /opt/astap -r 180

# With position hint:
/opt/astap_cli/astap_cli -f image.fits -fov 4.55 \
  -D d50 -d /opt/astap -ra 6.5 -spd 95.5 -r 10
```

> **Note:** ASTAP uses **SPD** (South Pole Distance) instead of Declination.
> `SPD = 90 + Dec` — e.g. Dec +5.5 = SPD 95.5, Dec -20 = SPD 70

### Manual RAW Conversion

```bash
# NEF to 16-bit grayscale TIFF:
dcraw -d -4 -T image.NEF

# TIFF to FITS:
python3 << 'EOF'
from astropy.io import fits
from PIL import Image
import numpy as np
img = Image.open('image.tiff')
data = np.array(img, dtype=np.uint16)
fits.PrimaryHDU(data).writeto('image.fits', overwrite=True)
EOF
```

---

## 7. Taking StarFinder Into the Field (VirtualBox)

StarFinder was built for portability — all hardware settings are VirtualBox-compatible.

### Step 1: Export the Disk
On DeepThought:
```bash
qemu-img convert -f qcow2 -O vdi \
  /mnt/nvme-2tb/images/103/vm-103-disk-0.qcow2 \
  /tmp/starfinder.vdi
```
Copy `starfinder.vdi` to a USB drive (~5-6 GB).

### Step 2: Create VM in VirtualBox

1. **New** > Name: StarFinder, Type: Linux, Debian 64-bit
2. Memory: **4096 MB**
3. Hard disk: **Use existing** > browse to `starfinder.vdi`
4. **Settings:**

| Setting | Value | Why |
|---------|-------|-----|
| Chipset | **PIIX3** | Matches Proxmox i440fx |
| Enable EFI | **UNCHECKED** | Must use legacy BIOS |
| Processors | **2** | Match Proxmox config |
| Network Adapter | **Intel PRO/1000 MT** | Matches E1000 |
| Attached to | **Host-only Adapter** | For field use without network |

### Step 3: Connect and Solve
```bash
# Find the VM's IP (at VirtualBox console):
ip addr show

# From laptop:
ssh root@<ip-address>
platesolve /root/photo.NEF --fov 4.55
```

### Shared Folders (no network needed)
1. Install once (with internet): `apt-get install virtualbox-guest-utils`
2. VirtualBox Settings > Shared Folders > add a laptop folder as `photos`
3. In the VM:
```bash
mkdir -p /mnt/photos
mount -t vboxsf photos /mnt/photos
platesolve /mnt/photos/photo.NEF
```

---

## 8. System Reference

### VM Specifications
| Spec | Value |
|------|-------|
| Name | StarFinder |
| Proxmox VMID | 103 |
| OS | Debian 12.12 (Bookworm) |
| Kernel | 6.1.0-39-amd64 |
| CPU | 2 cores |
| RAM | 4 GB |
| Disk | 32 GB (qcow2 on nvme-2tb) |
| BIOS | SeaBIOS (legacy) |
| Machine | i440fx |
| Network | Intel E1000, DHCP |

### Installed Software
| Software | Version | Path |
|----------|---------|------|
| Astrometry.net | 0.93 | `/usr/bin/solve-field` |
| ASTAP CLI | 2026.02.09 | `/opt/astap_cli/astap_cli` |
| dcraw | - | `/usr/bin/dcraw` |
| Python | 3.11 | `/usr/bin/python3` |
| Astropy | 5.2.1 | Python package |
| Flask Web UI | - | `/opt/starfinder-web/app.py` |
| platesolve | - | `/usr/local/bin/platesolve` |

### Star Databases
| Database | Location | Size | Coverage |
|----------|----------|------|----------|
| Tycho-2 (scales 7-19) | `/usr/share/astrometry/` | 285 MB | ~22 arcmin to ~33 deg, full sky |
| ASTAP D50 | `/opt/astap/` | 935 MB | ~0.2 to ~6 deg, full sky |

### Disk Usage
- OS + packages: ~5.5 GB
- Databases: ~1.2 GB
- Free space: ~24 GB

---

## 9. Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Did not solve" / PLTSOLVD=F** | Add `--fov`, `--ra`, `--dec` to narrow the search. Use RAW instead of JPG. Ensure image has visible stars. |
| **"No sources found"** | Image too dark or overcast. Use NEF instead of JPG. |
| **Solve takes >2 minutes** | Provide `--fov`, `--ra`, `--dec` to reduce search space. |
| **SSH refused** | Check VM is running. Check IP: `ip addr show` at console. |
| **Disk full** | Clean up: `rm -f /root/*.{axy,corr,match,rdls,wcs,solved,new,ini,fits,tiff}` |
| **VM won't boot in VirtualBox** | EFI must be UNCHECKED. Chipset: PIIX3. NIC: Intel PRO/1000. |
| **Shared folders not working** | Install `virtualbox-guest-utils` and reboot. |
| **Web UI not loading** | Check service: `systemctl status starfinder-web`. Restart: `systemctl restart starfinder-web`. |

---

*StarFinder Plate Solving Station — Built March 2026*
*Solvers: [Astrometry.net](https://astrometry.net) (Dustin Lang et al.) and [ASTAP](https://www.hnsky.org/astap.htm) (Han Kleijn)*
