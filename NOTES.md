# AstroDiscovery - Development Notes

## March 24, 2026 - Day 1: StarFinder VM and Initial Tools

- Created StarFinder VM (Proxmox VMID 103) on DeepThought server
  - Debian 12.12 (Bookworm), 2 CPU cores, 4 GB RAM, 32 GB disk
  - Configured for VirtualBox portability (SATA controller, VirtIO network)
- Installed Astrometry.net with Tycho-2 index files (scales 7-19, 285 MB)
- Installed ASTAP CLI with D50 star database (935 MB, 1476 files)
- Created `platesolve` CLI tool
  - Runs both solvers with chaining: Astrometry.net solves first, feeds coordinates to ASTAP as hint
  - Added solve timing to output
- Built Flask web UI with night-vision red theme (preserves dark adaptation)
  - Drag-and-drop file upload
  - NEF, CR2, FITS, JPG, TIFF, PNG support
  - FOV, RA, Dec input fields
  - Dual solver results display
  - Raw output toggle
- Deployed as systemd service on the VM
- Successfully solved 4 test NEF images from a Nikon D7200
- Created GitHub repository: astro-discovery
- Wrote initial user manual and Pi Zero design document

## March 25, 2026 - Day 2: Raspberry Pi Zero 2 W Field Deployment

- Set up Raspberry Pi Zero 2 W (Debian 13 Trixie, aarch64, 416 MB RAM, 29 GB SD)
- Configured USB gadget mode (Pi appears as USB Ethernet device at 10.42.1.1)
- Configured WiFi hotspot (SSID: AstroDiscovery, password: stargazer, IP: 10.42.0.1)
- Installed astrometry.net + Tycho-2 indexes from Debian repos
- Installed ASTAP CLI from Debian repos (arm64)
- Transferred D50 star database (861 MB) from StarFinder VM to Pi
- Deployed adapted `platesolve` script for Pi (uses `astap_cli` from /usr/bin)
- Installed gphoto2 - successfully communicates with Nikon D7200 over USB
  - Camera detection, file listing, file download all working
- Built enhanced web UI with:
  - **Upload tab**: drag-and-drop with solve (same as VM version)
  - **Camera tab**: browse camera files, one-tap download + solve
  - **Object identification**: Messier catalog (110 objects) - identifies objects in solved FOV
  - **Pointing error**: RA/Dec error + Az/El nudge directions (e.g., "Nudge LEFT 0.38, Nudge UP 0.19")
  - **GPS button**: gets location from iPhone for Az/El calculations
  - **Target input**: autocomplete for Messier objects + common names
  - Duplicate file filtering (camera writes to both card slots)
- Generated self-signed SSL certificate for HTTPS (enables GPS on iOS Safari)
  - Certificate installable as iOS profile via https://[ip]/cert
  - Valid for 10 years, covers all Pi network interfaces
- Fixed issues encountered during Pi deployment:
  - /tmp is tmpfs (209 MB) on Pi - moved uploads to /var/lib/astro-discovery/uploads
  - gphoto2 file listing regex did not match NEF files (no resolution field)
  - Camera download needed --force-overwrite and global index (not per-folder)
  - iOS Safari button onclick handling
  - Installed missing `bc` package for platesolve script
- Deployed as systemd service, auto-starts on boot
- Successfully solving star photos in ~80-100 seconds on Pi Zero 2 W
- Full end-to-end test: iPhone Safari -> Camera tab -> Solve -> Results with objects + pointing error
