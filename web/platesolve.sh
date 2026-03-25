#!/bin/bash
# AstroDiscovery Plate Solver - solves NEF/JPG/FITS images
# Runs Astrometry.net first, then feeds coordinates to ASTAP for a fast solve.
# Usage: platesolve <image> [--fov degrees] [--ra hours] [--dec degrees]

set -e

IMAGE="$1"
shift || true

FOV="4.55"
RA=""
DEC=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --fov) FOV="$2"; shift 2;;
        --ra) RA="$2"; shift 2;;
        --dec) DEC="$2"; shift 2;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

if [[ -z "$IMAGE" ]]; then
    echo "Usage: platesolve <image> [--fov degrees] [--ra hours] [--dec degrees]"
    exit 1
fi

BASENAME=$(basename "$IMAGE" | sed 's/\.[^.]*$//')
WORKDIR=$(dirname "$(readlink -f "$IMAGE")")
FITS_FILE=""
TOTAL_START=$(date +%s%N)

# Convert to FITS if needed
EXT="${IMAGE##*.}"
EXT_LOWER=$(echo "$EXT" | tr 'A-Z' 'a-z')

if [[ "$EXT_LOWER" == "nef" || "$EXT_LOWER" == "cr2" || "$EXT_LOWER" == "arw" ]]; then
    CONV_START=$(date +%s%N)
    echo "[*] Converting RAW to grayscale TIFF..."
    dcraw -d -4 -T "$IMAGE"
    TIFF_FILE="${IMAGE%.*}.tiff"
    echo "[*] Converting TIFF to FITS..."
    python3 << PYEOF
from astropy.io import fits
from PIL import Image
import numpy as np
img = Image.open("$TIFF_FILE")
data = np.array(img, dtype=np.uint16)
hdu = fits.PrimaryHDU(data)
hdu.writeto("${WORKDIR}/${BASENAME}.fits", overwrite=True)
print("FITS: %dx%d %s" % (data.shape[1], data.shape[0], data.dtype))
PYEOF
    FITS_FILE="${WORKDIR}/${BASENAME}.fits"
    rm -f "$TIFF_FILE"
    CONV_END=$(date +%s%N)
    CONV_MS=$(( (CONV_END - CONV_START) / 1000000 ))
    echo "[*] Conversion time: ${CONV_MS}ms"
elif [[ "$EXT_LOWER" == "fits" || "$EXT_LOWER" == "fit" ]]; then
    FITS_FILE="$IMAGE"
else
    FITS_FILE="$IMAGE"
fi

SOLVED_BASE="${FITS_FILE%.*}"
ASTRO_RA_DEG=""
ASTRO_DEC_DEG=""

# =========================================================================
#  ASTROMETRY.NET
# =========================================================================
echo ""
echo "========================================="
echo "  ASTROMETRY.NET"
echo "========================================="
SCALE_LO=$(echo "$FOV * 0.5" | bc)
SCALE_HI=$(echo "$FOV * 2" | bc)
CMD="solve-field --no-plots --overwrite --scale-units degwidth --scale-low $SCALE_LO --scale-high $SCALE_HI --downsample 2 --cpulimit 180"
if [[ -n "$RA" && -n "$DEC" ]]; then
    RA_DEG=$(echo "$RA * 15" | bc)
    CMD="$CMD --ra $RA_DEG --dec $DEC --radius 10"
fi
echo "[*] $CMD $FITS_FILE"
ASTRO_START=$(date +%s%N)
$CMD "$FITS_FILE" 2>&1 | grep -E "^(Field|Did not|simplexy)" || true
ASTRO_END=$(date +%s%N)
ASTRO_MS=$(( (ASTRO_END - ASTRO_START) / 1000000 ))

if [[ -f "${SOLVED_BASE}.solved" ]]; then
    echo "[+] SOLVED!  (${ASTRO_MS}ms)"
    PYOUT=$(python3 << PYEOF
from astropy.io import fits
import math
h = fits.open("${SOLVED_BASE}.wcs")[0].header
ra = h.get("CRVAL1", 0)
dec = h.get("CRVAL2", 0)
ra_h = ra / 15.0
ra_hh = int(ra_h)
ra_mm = int((ra_h - ra_hh) * 60)
ra_ss = ((ra_h - ra_hh) * 60 - ra_mm) * 60
dec_sign = "+" if dec >= 0 else "-"
dec_abs = abs(dec)
dec_dd = int(dec_abs)
dec_mm = int((dec_abs - dec_dd) * 60)
dec_ss = ((dec_abs - dec_dd) * 60 - dec_mm) * 60
cd11 = h.get("CD1_1", 0)
cd12 = h.get("CD1_2", 0)
scale = math.sqrt(cd11**2 + cd12**2) * 3600
w = h.get("IMAGEW", 1)
ht = h.get("IMAGEH", 1)
fov_w = w * scale / 3600
fov_h = ht * scale / 3600
print("DISPLAY:  Center RA:  %02dh %02dm %05.2fs" % (ra_hh, ra_mm, ra_ss))
print("DISPLAY:  Center Dec: %s%02dd %02dm %05.2fs" % (dec_sign, dec_dd, dec_mm, dec_ss))
print("DISPLAY:  Scale: %.2f arcsec/pix" % scale)
print("DISPLAY:  FOV: %.2f x %.2f deg" % (fov_w, fov_h))
print("EXPORT:ASTRO_RA_DEG=%.6f" % ra)
print("EXPORT:ASTRO_DEC_DEG=%.6f" % dec)
print("EXPORT:ASTRO_FOV=%.4f" % fov_w)
PYEOF
)
    echo "$PYOUT" | grep "^DISPLAY:" | sed 's/^DISPLAY://'
    eval "$(echo "$PYOUT" | grep "^EXPORT:" | sed 's/^EXPORT:/export /')"
else
    echo "[-] Failed to solve  (${ASTRO_MS}ms)"
fi

# =========================================================================
#  ASTAP
# =========================================================================
echo ""
echo "========================================="
echo "  ASTAP"
echo "========================================="

ASTAP_CMD="astap_cli -f $FITS_FILE -D d50 -d /opt/astap"

if [[ -n "$ASTRO_RA_DEG" && -n "$ASTRO_DEC_DEG" ]]; then
    ASTAP_RA_H=$(echo "$ASTRO_RA_DEG / 15" | bc -l)
    ASTAP_SPD=$(echo "90 + $ASTRO_DEC_DEG" | bc -l)
    ASTAP_FOV_USE="${ASTRO_FOV:-$FOV}"
    ASTAP_CMD="$ASTAP_CMD -fov $ASTAP_FOV_USE -ra $ASTAP_RA_H -spd $ASTAP_SPD -r 5"
    echo "[*] Using Astrometry.net solution as hint"
elif [[ -n "$RA" && -n "$DEC" ]]; then
    SPD=$(echo "90 + $DEC" | bc)
    ASTAP_CMD="$ASTAP_CMD -fov $FOV -ra $RA -spd $SPD -r 10"
    echo "[*] Using user-provided coordinates as hint"
else
    ASTAP_CMD="$ASTAP_CMD -fov $FOV -r 180"
    echo "[*] Blind solve (no hints available)"
fi

echo "[*] $ASTAP_CMD"
ASTAP_START=$(date +%s%N)
$ASTAP_CMD 2>&1 | grep -E "^(Solution|Solved|Warning|ERROR|Using)" || true
ASTAP_END=$(date +%s%N)
ASTAP_MS=$(( (ASTAP_END - ASTAP_START) / 1000000 ))

if [[ -f "${SOLVED_BASE}.ini" ]] && grep -q "PLTSOLVD=T" "${SOLVED_BASE}.ini" 2>/dev/null; then
    echo "[+] ASTAP result:  (${ASTAP_MS}ms)"
    grep -E "^(CRVAL|CDELT|PLTSOLVD)" "${SOLVED_BASE}.ini" 2>/dev/null || true
else
    echo "[-] ASTAP failed  (${ASTAP_MS}ms)"
fi

# =========================================================================
#  SUMMARY
# =========================================================================
TOTAL_END=$(date +%s%N)
TOTAL_MS=$(( (TOTAL_END - TOTAL_START) / 1000000 ))
TOTAL_SEC=$(echo "scale=1; $TOTAL_MS / 1000" | bc)
echo ""
echo "========================================="
echo "  Total time: ${TOTAL_SEC}s"
echo "========================================="
