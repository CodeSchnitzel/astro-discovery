#!/usr/bin/env python3
"""AstroDiscovery Web UI - Plate Solving + Camera + Object ID + Pointing Error."""
import os, re, subprocess, uuid, json, math
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
UPLOAD_DIR = '/var/lib/astro-discovery/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {'nef','cr2','arw','fits','fit','jpg','jpeg','tiff','tif','png'}

# Messier catalog: (name, RA_deg, Dec_deg, common_name)
MESSIER_CATALOG = [
("M1",83.6331,22.0145,"Crab Nebula"),("M2",323.3626,-0.8233,""),("M3",205.5484,28.3773,""),
("M4",245.8968,-26.5258,""),("M5",229.6384,2.0811,""),("M6",265.0834,-32.2167,"Butterfly Cluster"),
("M7",268.4667,-34.7933,"Ptolemy Cluster"),("M8",270.9042,-24.3867,"Lagoon Nebula"),
("M9",259.7998,-18.5161,""),("M10",254.2877,-4.1003,""),("M11",282.7667,-6.2667,"Wild Duck Cluster"),
("M12",251.8092,-1.9483,""),("M13",250.4217,36.4613,"Great Hercules Cluster"),
("M14",264.4004,-3.2458,""),("M15",322.4930,12.1670,""),("M16",274.7000,-13.8067,"Eagle Nebula"),
("M17",275.1917,-16.1733,"Omega Nebula"),("M18",275.2375,-17.1300,""),
("M19",255.6570,-26.2681,""),("M20",270.6208,-23.0300,"Trifid Nebula"),
("M21",270.9833,-22.4900,""),("M22",279.0998,-23.9047,""),("M23",269.2667,-19.0167,""),
("M24",274.5250,-18.4167,"Sagittarius Star Cloud"),("M25",277.9042,-19.2500,""),
("M26",281.3208,-9.3833,""),("M27",299.9015,22.7211,"Dumbbell Nebula"),
("M28",276.1363,-24.8703,""),("M29",305.9833,38.5167,""),("M30",325.0922,-23.1797,""),
("M31",10.6848,41.2688,"Andromeda Galaxy"),("M32",10.6743,40.8652,""),
("M33",23.4621,30.6602,"Triangulum Galaxy"),("M34",40.5167,42.7833,""),
("M35",92.2500,24.3500,""),("M36",84.0833,34.1333,""),("M37",88.0708,32.5500,""),
("M38",82.1708,35.8333,""),("M39",323.0583,48.4333,""),
("M40",185.5500,58.0833,"Winnecke 4"),("M41",101.5042,-20.7567,""),
("M42",83.8221,-5.3911,"Orion Nebula"),("M43",83.8900,-5.2700,"De Mairan's Nebula"),
("M44",130.0500,19.6200,"Beehive Cluster"),("M45",56.8500,24.1167,"Pleiades"),
("M46",115.4667,-14.8167,""),("M47",114.1500,-14.4833,""),("M48",123.4333,-5.7333,""),
("M49",187.4449,8.0003,""),("M50",105.6917,-8.3667,""),
("M51",202.4696,47.1952,"Whirlpool Galaxy"),("M52",351.2083,61.5833,""),
("M53",198.2302,18.1681,""),("M54",283.7636,-30.4783,""),("M55",294.9988,-30.9642,""),
("M56",289.1483,30.1836,""),("M57",283.3963,33.0289,"Ring Nebula"),
("M58",189.4313,11.8183,""),("M59",190.5092,11.6472,""),("M60",190.9163,11.5528,""),
("M61",185.4790,4.4739,""),("M62",255.3032,-30.1136,""),
("M63",198.9553,42.0293,"Sunflower Galaxy"),("M64",194.1826,21.6828,"Black Eye Galaxy"),
("M65",169.7330,13.0922,""),("M66",170.0626,12.9914,""),("M67",132.8500,11.8167,""),
("M68",189.8667,-26.7444,""),("M69",277.8461,-32.3481,""),("M70",280.8035,-32.2922,""),
("M71",298.4438,18.7792,""),("M72",313.3654,-12.5372,""),("M73",314.7500,-12.6333,""),
("M74",24.1740,15.7836,"Phantom Galaxy"),("M75",301.5200,-21.9211,""),
("M76",25.5817,51.5753,"Little Dumbbell"),("M77",40.6696,-0.0133,"Cetus A"),
("M78",86.6500,0.0833,""),("M79",81.0462,-24.5247,""),("M80",244.2601,-22.9753,""),
("M81",148.8882,69.0653,"Bode's Galaxy"),("M82",148.9685,69.6797,"Cigar Galaxy"),
("M83",204.2538,-29.8653,"Southern Pinwheel"),("M84",186.2656,12.8869,""),
("M85",186.3502,18.1911,""),("M86",186.5509,12.9461,""),
("M87",187.7059,12.3911,"Virgo A"),("M88",187.9968,14.4203,""),
("M89",188.9159,12.5564,""),("M90",189.2093,13.1631,""),("M91",188.8600,14.4964,""),
("M92",259.2808,43.1364,""),("M93",116.1333,-23.8500,""),("M94",192.7215,41.1203,""),
("M95",160.9898,11.7039,""),("M96",161.6907,11.8194,""),
("M97",168.6986,55.0192,"Owl Nebula"),("M98",183.4513,14.9003,""),
("M99",184.7063,14.4164,""),("M100",185.7287,15.8222,""),
("M101",210.8023,54.3490,"Pinwheel Galaxy"),("M102",226.6232,55.7633,"Spindle Galaxy"),
("M103",23.3417,60.6500,""),("M104",189.9976,-11.6231,"Sombrero Galaxy"),
("M105",161.9565,12.5817,""),("M106",184.7397,47.3039,""),("M107",248.1333,-13.0536,""),
("M108",167.8796,55.6741,""),("M109",179.3999,53.3744,""),("M110",10.0918,41.6853,""),
]

def angular_separation(ra1, dec1, ra2, dec2):
    ra1,dec1,ra2,dec2 = map(math.radians,[ra1,dec1,ra2,dec2])
    a = math.sin((dec2-dec1)/2)**2 + math.cos(dec1)*math.cos(dec2)*math.sin((ra2-ra1)/2)**2
    return math.degrees(2*math.asin(min(1,math.sqrt(a))))

def find_objects_in_fov(ra_c, dec_c, fov_w, fov_h):
    radius = math.sqrt(fov_w**2 + fov_h**2)/2
    found = []
    for name,ra,dec,common in MESSIER_CATALOG:
        sep = angular_separation(ra_c,dec_c,ra,dec)
        if sep <= radius:
            label = f"{name} ({common})" if common else name
            found.append({"name":label,"separation":round(sep,3)})
    found.sort(key=lambda x: x["separation"])
    return found

def deg_to_dms(deg):
    sign = "+" if deg>=0 else "-"; deg=abs(deg)
    d=int(deg); m=int((deg-d)*60); s=((deg-d)*60-m)*60
    return f"{sign}{d} deg {m:02d}' {s:04.1f}\""

def compute_pointing_error(ra_c,dec_c,tra,tdec,lat=None,lon=None,obs_time=None):
    dra = tra-ra_c
    if dra>180: dra-=360
    if dra<-180: dra+=360
    dra_cos = dra*math.cos(math.radians(dec_c))
    ddec = tdec-dec_c
    result = {"ra_error_deg":round(dra_cos,4),"dec_error_deg":round(ddec,4),
              "ra_error_str":deg_to_dms(dra_cos),"dec_error_str":deg_to_dms(ddec),
              "total_sep_deg":round(angular_separation(ra_c,dec_c,tra,tdec),4)}
    if lat is not None and lon is not None:
        try:
            from astropy.coordinates import SkyCoord,EarthLocation,AltAz
            from astropy.time import Time
            import astropy.units as u
            loc = EarthLocation(lat=lat*u.deg,lon=lon*u.deg)
            t = Time(obs_time) if obs_time else Time.now()
            frame = AltAz(obstime=t,location=loc)
            cur = SkyCoord(ra=ra_c*u.deg,dec=dec_c*u.deg).transform_to(frame)
            tgt = SkyCoord(ra=tra*u.deg,dec=tdec*u.deg).transform_to(frame)
            daz = (tgt.az-cur.az).deg
            if daz>180: daz-=360
            if daz<-180: daz+=360
            dalt = (tgt.alt-cur.alt).deg
            az_dir = "RIGHT" if daz>0 else "LEFT"
            el_dir = "UP" if dalt>0 else "DOWN"
            result["az_error_deg"]=round(daz,4)
            result["el_error_deg"]=round(dalt,4)
            result["az_nudge"]=f"Nudge {az_dir} {abs(daz):.2f} deg"
            result["el_nudge"]=f"Nudge {el_dir} {abs(dalt):.2f} deg"
        except Exception as e:
            result["altaz_error"]=str(e)
    return result

def lookup_target(name):
    nl = name.strip().lower()
    for mname,ra,dec,common in MESSIER_CATALOG:
        if nl==mname.lower(): return (ra,dec,f"{mname} ({common})" if common else mname)
        if common and nl==common.lower(): return (ra,dec,f"{mname} ({common})")
    return None

def parse_astrometry_output(text):
    result = {'solved':False}
    if '[+] SOLVED!' in text:
        result['solved']=True
        m=re.search(r'\[\+\] SOLVED!\s*\((\d+)ms\)',text)
        if m: result['solve_time']='%.1fs'%(int(m.group(1))/1000.0)
        for line in text.split('\n'):
            line=line.strip()
            if line.startswith('Center RA:'): result['ra']=line.split(':',1)[1].strip()
            elif line.startswith('Center Dec:'): result['dec']=line.split(':',1)[1].strip()
            elif line.startswith('Scale:'): result['scale']=line.split(':',1)[1].strip()
            elif line.startswith('FOV:'): result['fov']=line.split(':',1)[1].strip()
    else:
        m=re.search(r'\[\-\] Failed to solve\s*\((\d+)ms\)',text)
        if m: result['solve_time']='%.1fs'%(int(m.group(1))/1000.0)
    return result

def parse_astap_output(text):
    result = {'solved':False}
    for line in text.split('\n'):
        line=line.strip()
        if 'PLTSOLVD=T' in line: result['solved']=True
        m=re.search(r'Solution found:\s*(.+)',line)
        if m: result['position']=m.group(1).strip()
        if line.startswith('Warning'): result['fov_warning']=line
        m2=re.search(r'\((\d+)ms\)',line)
        if m2 and ('ASTAP result' in line or 'ASTAP failed' in line):
            result['solve_time']='%.1fs'%(int(m2.group(1))/1000.0)
    if 'Using Astrometry.net solution as hint' in text: result['chained']=True
    return result

def extract_solved_coords(raw):
    ra=dec=fov_w=None
    for line in raw.split('\n'):
        m=re.search(r'EXPORT:ASTRO_RA_DEG=([\d.eE+-]+)',line)
        if m: ra=float(m.group(1))
        m=re.search(r'EXPORT:ASTRO_DEC_DEG=([\d.eE+-]+)',line)
        if m: dec=float(m.group(1))
        m=re.search(r'EXPORT:ASTRO_FOV=([\d.eE+-]+)',line)
        if m: fov_w=float(m.group(1))
    return ra,dec,fov_w,(fov_w*2.0/3.0 if fov_w else None)

# ======================== CAMERA API ========================


@app.route('/cert')
def download_cert():
    return app.send_static_file('cert.pem') if os.path.exists('static/cert.pem') else            open('/opt/astro-discovery/certs/cert.pem').read(), 200, {
               'Content-Type': 'application/x-x509-ca-cert',
               'Content-Disposition': 'attachment; filename=AstroDiscovery.crt'
           }

@app.route('/api/camera/detect')
def camera_detect():
    try:
        p=subprocess.run(['gphoto2','--auto-detect'],capture_output=True,text=True,timeout=10)
        cams=[l.strip() for l in p.stdout.strip().split('\n')[2:] if l.strip()]
        return jsonify({'connected':len(cams)>0,'cameras':cams})
    except Exception as e:
        return jsonify({'connected':False,'error':str(e)})

@app.route('/api/camera/files')
def camera_files():
    try:
        p=subprocess.run(['gphoto2','--list-files'],capture_output=True,text=True,timeout=30)
        files=[]
        seen=set()
        for line in p.stdout.split('\n'):
            m=re.match(r'#(\d+)\s+(\S+)\s+\w+\s+(\d+)\s+KB',line)
            if m and m.group(2) not in seen:
                seen.add(m.group(2))
                files.append({'index':int(m.group(1)),'name':m.group(2),'size_kb':int(m.group(3)),'resolution':''})
        return jsonify({'files':files})
    except Exception as e:
        return jsonify({'error':str(e)})

@app.route('/api/camera/download-and-solve/<int:index>',methods=['POST'])
def camera_download_and_solve(index):
    try:
        job_id=str(uuid.uuid4())[:8]; job_dir=os.path.join(UPLOAD_DIR,job_id); os.makedirs(job_dir,exist_ok=True)
        proc=subprocess.run(["gphoto2","--force-overwrite","--get-file",str(index)],capture_output=True,text=True,timeout=120,cwd=job_dir)
        downloaded=[f for f in os.listdir(job_dir) if not f.startswith('.')]
        if not downloaded: return jsonify({'error':'No file downloaded'})
        filepath=os.path.join(job_dir,downloaded[0])
        data=request.get_json(silent=True) or {}
        cmd=['platesolve',filepath,'--fov',str(data.get('fov','4.55'))]
        if data.get('ra'): cmd.extend(['--ra',str(data['ra'])])
        if data.get('dec'): cmd.extend(['--dec',str(data['dec'])])
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
        output=proc.stdout+proc.stderr
        return _parse_solve_output(downloaded[0], output)
    except Exception as e:
        return jsonify({'error':str(e)})

# ======================== POINTING ERROR API ========================

@app.route('/api/pointing-error',methods=['POST'])
def pointing_error():
    data=request.get_json()
    if not data: return jsonify({'error':'No data'}),400
    ra_c=data.get('ra_deg'); dec_c=data.get('dec_deg')
    if ra_c is None: return jsonify({'error':'Need solved coords'}),400
    target=lookup_target(data.get('target',''))
    if not target: return jsonify({'error':f"Unknown target: {data.get('target','')}"}),400
    tra,tdec,tlabel=target
    result=compute_pointing_error(ra_c,dec_c,tra,tdec,lat=data.get('lat'),lon=data.get('lon'),obs_time=data.get('obs_time'))
    result['target']=tlabel
    return jsonify(result)

# ======================== SOLVE ENDPOINT ========================

@app.route('/solve',methods=['POST'])
def solve():
    if 'file' not in request.files: return jsonify({'error':'No file uploaded'}),400
    f=request.files['file']
    if not f.filename: return jsonify({'error':'No file selected'}),400
    ext=f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else ''
    if ext not in ALLOWED_EXTENSIONS: return jsonify({'error':f'Unsupported: .{ext}'}),400
    job_id=str(uuid.uuid4())[:8]; job_dir=os.path.join(UPLOAD_DIR,job_id); os.makedirs(job_dir,exist_ok=True)
    filepath=os.path.join(job_dir,f.filename); f.save(filepath)
    fov=request.form.get('fov','4.55'); cmd=['platesolve',filepath,'--fov',fov]
    ra=request.form.get('ra','').strip(); dec=request.form.get('dec','').strip()
    if ra: cmd.extend(['--ra',ra])
    if dec: cmd.extend(['--dec',dec])
    try:
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
        output=proc.stdout+proc.stderr
    except subprocess.TimeoutExpired:
        return jsonify({'error':'Timeout after 10 min'}),500
    except Exception as e:
        return jsonify({'error':str(e)}),500
    result = _parse_solve_output(f.filename, output)
    try:
        import shutil; shutil.rmtree(job_dir,ignore_errors=True)
    except: pass
    return result

def _parse_solve_output(filename, output):
    sections=re.split(r'={3,}',output); astro_text=astap_text=''
    for i,s in enumerate(sections):
        if 'ASTROMETRY' in s and not astro_text and i+1<len(sections): astro_text=sections[i+1]
        elif 'ASTAP' in s and not astap_text and i+1<len(sections): astap_text=sections[i+1]
    total_time=''; m=re.search(r'Total time:\s*(\S+)',output)
    if m: total_time=m.group(1)
    ra_deg,dec_deg,fov_w,fov_h=extract_solved_coords(output)
    objects=find_objects_in_fov(ra_deg,dec_deg,fov_w,fov_h or fov_w*0.67) if ra_deg and fov_w else []
    return jsonify({'filename':filename,'astrometry':parse_astrometry_output(astro_text),
        'astap':parse_astap_output(astap_text),'total_time':total_time,'objects':objects,
        'solved_ra_deg':ra_deg,'solved_dec_deg':dec_deg,'raw_output':output})

# ======================== HTML ========================

# Build target list for autocomplete
_target_list_js = ','.join([
    '"%s"' % (f"{n} ({c})" if c else n)
    for n,_,_,c in MESSIER_CATALOG
])

HTML_PAGE = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no"><title>AstroDiscovery</title>
<style>
:root{--bg:#0a0000;--surface:#1a0505;--border:#3a1515;--red:#8b2020;--red-bright:#cc3333;--red-dim:#551111;--text:#cc8888;--text-bright:#eecccc;--text-dim:#775555;--success:#338833;--success-text:#88cc88;--blue:#335588;--blue-text:#88aacc}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:16px}
h1{text-align:center;color:var(--red-bright);font-size:1.5em;margin-bottom:4px;letter-spacing:2px}.subtitle{text-align:center;color:var(--text-dim);font-size:.85em;margin-bottom:16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}
.tabs{display:flex;gap:0;margin-bottom:16px}.tab{flex:1;padding:12px;text-align:center;background:var(--surface);border:1px solid var(--border);color:var(--text-dim);cursor:pointer;font-weight:bold;font-size:.9em}.tab:first-child{border-radius:12px 0 0 12px}.tab:last-child{border-radius:0 12px 12px 0}.tab.active{background:var(--red-dim);color:var(--red-bright);border-color:var(--red)}
.tab-content{display:none}.tab-content.active{display:block}
.dropzone{border:2px dashed var(--red);border-radius:12px;padding:40px 20px;text-align:center;cursor:pointer;transition:all .2s}.dropzone.dragover{border-color:var(--red-bright);background:var(--red-dim)}.dropzone.has-file{border-color:var(--success);border-style:solid}
.dropzone-icon{font-size:2.5em;margin-bottom:8px}.dropzone-text{color:var(--text);font-size:1.1em}.dropzone-hint{color:var(--text-dim);font-size:.8em;margin-top:6px}.filename{color:var(--text-bright);font-weight:bold}#fileInput{display:none}
.options{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.options label{display:block;color:var(--text-dim);font-size:.75em;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.options input,.loc-input input{width:100%%;padding:10px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text-bright);font-size:1em;text-align:center}
.options input::placeholder,.loc-input input::placeholder{color:var(--text-dim)}.options input:focus,.loc-input input:focus{outline:none;border-color:var(--red)}
.loc-section{margin-top:12px}.loc-row{display:grid;grid-template-columns:1fr 1fr auto;gap:10px;align-items:end}.loc-input label{display:block;color:var(--text-dim);font-size:.75em;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.gps-btn{padding:10px 16px;background:var(--blue);color:var(--blue-text);border:none;border-radius:8px;cursor:pointer;font-size:.8em;white-space:nowrap}.gps-btn:hover{background:#4477aa}
.target-section{margin-top:12px}.target-input{width:100%%;padding:10px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text-bright);font-size:1em}.target-input::placeholder{color:var(--text-dim)}
.solve-btn{display:block;width:100%%;padding:16px;background:var(--red);color:var(--text-bright);border:none;border-radius:12px;font-size:1.2em;font-weight:bold;cursor:pointer;letter-spacing:1px;margin-top:12px}.solve-btn:hover{background:var(--red-bright)}.solve-btn:disabled{background:var(--red-dim);color:var(--text-dim);cursor:not-allowed}
.spinner{display:none;text-align:center;padding:30px}.spinner.active{display:block}.spinner-dot{display:inline-block;width:12px;height:12px;background:var(--red-bright);border-radius:50%%;margin:0 4px;animation:pulse 1.4s infinite ease-in-out}.spinner-dot:nth-child(2){animation-delay:.2s}.spinner-dot:nth-child(3){animation-delay:.4s}@keyframes pulse{0%%,80%%,100%%{transform:scale(.6);opacity:.4}40%%{transform:scale(1);opacity:1}}.spinner-text{color:var(--text-dim);margin-top:12px;font-size:.9em}
.results{display:none}.results.active{display:block}.result-header{color:var(--red-bright);font-size:1.1em;font-weight:bold;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.result-grid{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin-bottom:12px}.result-label{color:var(--text-dim);font-size:.8em;text-transform:uppercase;letter-spacing:1px;padding:3px 0}.result-value{color:var(--text-bright);font-family:'SF Mono','Consolas',monospace;font-size:1em;padding:3px 0}
.solver-section{margin-bottom:16px}.solver-name{color:var(--text);font-weight:bold;font-size:.95em;margin-bottom:6px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75em;font-weight:bold;text-transform:uppercase}.badge.solved{background:var(--success);color:#fff}.badge.failed{background:var(--red-dim);color:var(--red-bright)}
.objects-section{margin-top:12px;padding-top:12px;border-top:1px solid var(--border)}.objects-title{color:var(--blue-text);font-weight:bold;font-size:.9em;margin-bottom:8px}.object-tag{display:inline-block;padding:4px 10px;margin:3px;background:var(--blue);color:var(--blue-text);border-radius:6px;font-size:.85em}
.pointing-section{margin-top:12px;padding:12px;background:var(--bg);border:1px solid var(--border);border-radius:8px}.pointing-title{color:var(--red-bright);font-weight:bold;margin-bottom:8px}
.camera-list{max-height:400px;overflow-y:auto}.camera-file{display:flex;justify-content:space-between;align-items:center;padding:10px;border-bottom:1px solid var(--border)}.camera-file:last-child{border-bottom:none}.camera-file-name{color:var(--text-bright);font-family:monospace}.camera-file-info{color:var(--text-dim);font-size:.8em}.camera-file-btn{padding:6px 14px;background:var(--red);color:var(--text-bright);border:none;border-radius:6px;cursor:pointer;font-size:.85em}.camera-file-btn:hover{background:var(--red-bright)}.camera-status{text-align:center;padding:20px;color:var(--text-dim)}
.raw-output{margin-top:10px;padding:10px;background:var(--bg);border:1px solid var(--border);border-radius:8px;font-family:monospace;font-size:.7em;color:var(--text-dim);white-space:pre-wrap;word-break:break-all;max-height:200px;overflow-y:auto;display:none}
.toggle-raw{background:none;border:1px solid var(--border);color:var(--text-dim);padding:6px 12px;border-radius:6px;font-size:.8em;cursor:pointer;margin-top:8px}
.error-msg{display:none;background:var(--red-dim);border:1px solid var(--red);border-radius:8px;padding:12px;color:var(--red-bright);text-align:center}.error-msg.active{display:block}
</style></head><body>
<h1>&#9733; ASTRODISCOVERY</h1><p class="subtitle">Plate Solving Station</p>
<div class="tabs"><div class="tab active" onclick="switchTab('upload')">Upload</div><div class="tab" onclick="switchTab('camera')">Camera</div></div>
<div class="tab-content active" id="tab-upload">
<div class="card"><div class="dropzone" id="dropzone"><div class="dropzone-icon" id="dzIcon">&#9733;</div><div class="dropzone-text" id="dzText">Tap to select or drop image here</div><div class="dropzone-hint" id="dzHint">NEF &bull; CR2 &bull; FITS &bull; JPG &bull; TIFF &bull; PNG</div></div><input type="file" id="fileInput" accept=".nef,.cr2,.arw,.fits,.fit,.jpg,.jpeg,.tiff,.tif,.png"></div>
<div class="card"><div class="options"><div><label>FOV (deg)</label><input type="number" id="fov" value="4.55" step="0.01" min="0.1" max="180"></div><div><label>RA (hrs)</label><input type="number" id="ra" step="0.1" min="0" max="24" placeholder="optional"></div><div><label>Dec (deg)</label><input type="number" id="dec" step="0.1" min="-90" max="90" placeholder="optional"></div></div>
<div class="loc-section"><div class="loc-row"><div class="loc-input"><label>Latitude</label><input type="number" id="lat" step="0.001" min="-90" max="90" placeholder="for az/el"></div><div class="loc-input"><label>Longitude</label><input type="number" id="lon" step="0.001" min="-180" max="180" placeholder="for az/el"></div><button class="gps-btn" onclick="getGPS()">GPS</button></div></div>
<div class="target-section"><input class="target-input" id="target" placeholder="Target (e.g. M31, Orion Nebula)" list="targetList"><datalist id="targetList"></datalist></div></div>
<button class="solve-btn" id="solveBtn" disabled onclick="doSolve()">SOLVE</button>
</div>
<div class="tab-content" id="tab-camera"><div class="card"><div class="camera-status" id="cameraStatus">Tap to check camera...</div><div class="camera-list" id="cameraList" style="display:none"></div><button class="solve-btn" style="margin-top:12px" onclick="loadCamera()">Refresh Camera</button></div>
<div class="card"><div class="options"><div><label>FOV (deg)</label><input type="number" id="cam-fov" value="4.55" step="0.01"></div><div><label>RA (hrs)</label><input type="number" id="cam-ra" step="0.1" placeholder="optional"></div><div><label>Dec (deg)</label><input type="number" id="cam-dec" step="0.1" placeholder="optional"></div></div></div></div>
<div class="spinner" id="spinner"><div><span class="spinner-dot"></span><span class="spinner-dot"></span><span class="spinner-dot"></span></div><div class="spinner-text" id="spinnerText">Processing...</div></div>
<div class="error-msg" id="errorMsg"></div>
<div class="results card" id="results"></div>
<script>
let selectedFile=null,solvedRaDeg=null,solvedDecDeg=null;
const targets=[%s];
const dl=document.getElementById('targetList');targets.forEach(t=>{const o=document.createElement('option');o.value=t;dl.appendChild(o)});
function switchTab(tab){document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('active',tab==='upload'?i===0:i===1));document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));document.getElementById('tab-'+tab).classList.add('active');if(tab==='camera')loadCamera()}
const dropzone=document.getElementById('dropzone'),fileInput=document.getElementById('fileInput');
dropzone.addEventListener('click',()=>fileInput.click());dropzone.addEventListener('dragover',e=>{e.preventDefault();dropzone.classList.add('dragover')});dropzone.addEventListener('dragleave',()=>dropzone.classList.remove('dragover'));dropzone.addEventListener('drop',e=>{e.preventDefault();dropzone.classList.remove('dragover');if(e.dataTransfer.files.length)selectFile(e.dataTransfer.files[0])});fileInput.addEventListener('change',()=>{if(fileInput.files.length)selectFile(fileInput.files[0])});
function selectFile(file){selectedFile=file;dropzone.classList.add('has-file');document.getElementById('dzIcon').textContent='\\u2713';document.getElementById('dzText').innerHTML='<span class="filename">'+file.name+'</span>';document.getElementById('dzHint').innerHTML=(file.size/1024/1024).toFixed(1)+' MB';document.getElementById('solveBtn').disabled=false}
function getGPS(){if(!navigator.geolocation)return alert('GPS not available');navigator.geolocation.getCurrentPosition(p=>{document.getElementById('lat').value=p.coords.latitude.toFixed(4);document.getElementById('lon').value=p.coords.longitude.toFixed(4)},e=>alert('GPS error: '+e.message),{enableHighAccuracy:true})}
async function doSolve(){if(!selectedFile)return;document.getElementById('solveBtn').disabled=true;showSpinner('Solving...');const fd=new FormData();fd.append('file',selectedFile);fd.append('fov',document.getElementById('fov').value||'4.55');const ra=document.getElementById('ra').value,dec=document.getElementById('dec').value;if(ra)fd.append('ra',ra);if(dec)fd.append('dec',dec);try{const resp=await fetch('/solve',{method:'POST',body:fd});const data=await resp.json();hideSpinner();if(data.error){showError(data.error);return}solvedRaDeg=data.solved_ra_deg;solvedDecDeg=data.solved_dec_deg;showResults(data);const target=document.getElementById('target').value;if(target&&solvedRaDeg!=null)computePointing(target)}catch(e){hideSpinner();showError(e.message)}document.getElementById('solveBtn').disabled=false}
async function loadCamera(){const status=document.getElementById('cameraStatus'),list=document.getElementById('cameraList');status.textContent='Checking camera...';list.style.display='none';try{const r=await fetch('/api/camera/detect');const d=await r.json();if(!d.connected){status.textContent='No camera detected. Check USB.';return}status.textContent=d.cameras[0]||'Camera connected';const fr=await fetch('/api/camera/files');const fd=await fr.json();if(!fd.files||!fd.files.length){status.textContent+=' - No files on card';return}list.innerHTML='';for(var i=0;i<fd.files.length;i++){(function(f){var div=document.createElement('div');div.className='camera-file';var info=document.createElement('div');info.innerHTML='<div class="camera-file-name">'+f.name+'</div><div class="camera-file-info">'+(f.size_kb/1024).toFixed(1)+' MB</div>';div.appendChild(info);var btn=document.createElement('button');btn.className='camera-file-btn';btn.style.cursor='pointer';btn.style.webkitTapHighlightColor='rgba(204,51,51,0.3)';btn.textContent='Solve';btn.onclick=function(){cameraSolve(f.index,f.name);return false};div.appendChild(btn);list.appendChild(div)})(fd.files[i])}list.style.display='block'}catch(e){status.textContent='Error: '+e.message}}
async function cameraSolve(index,name){showSpinner('Downloading '+name+'...');try{const body={fov:document.getElementById('cam-fov').value||'4.55'};const ra=document.getElementById('cam-ra').value,dec=document.getElementById('cam-dec').value;if(ra)body.ra=ra;if(dec)body.dec=dec;document.getElementById('spinnerText').textContent='Solving '+name+'...';const r=await fetch('/api/camera/download-and-solve/'+index,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();hideSpinner();if(d.error){showError(d.error);return}solvedRaDeg=d.solved_ra_deg;solvedDecDeg=d.solved_dec_deg;showResults(d)}catch(e){hideSpinner();showError(e.message)}}
async function computePointing(targetName){if(solvedRaDeg==null)return;const body={ra_deg:solvedRaDeg,dec_deg:solvedDecDeg,target:targetName};const lat=document.getElementById('lat'),lon=document.getElementById('lon');if(lat&&lat.value)body.lat=parseFloat(lat.value);if(lon&&lon.value)body.lon=parseFloat(lon.value);try{const r=await fetch('/api/pointing-error',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(d.error)return;let html='<div class="pointing-section"><div class="pointing-title">Pointing Error to '+esc(d.target)+'</div><div class="result-grid">'+row('RA error',d.ra_error_str)+row('Dec error',d.dec_error_str)+row('Total offset',d.total_sep_deg+' deg');if(d.az_nudge)html+=row('Azimuth',d.az_nudge)+row('Elevation',d.el_nudge);html+='</div></div>';document.getElementById('results').innerHTML+=html}catch(e){}}
function showResults(data){let html='<div class="result-header">Results: '+esc(data.filename)+'</div>';if(data.astrometry){const a=data.astrometry,t=a.solve_time?' ('+a.solve_time+')':'';html+='<div class="solver-section"><div class="solver-name">Astrometry.net <span class="badge '+(a.solved?'solved">SOLVED'+t:'failed">FAILED'+t)+'</span></div>';if(a.solved)html+='<div class="result-grid">'+row('Center RA',a.ra)+row('Center Dec',a.dec)+row('Scale',a.scale)+row('Field of View',a.fov)+'</div>';html+='</div>'}if(data.astap){const t=data.astap,ts=t.solve_time?' ('+t.solve_time+')':'',ch=t.chained?' <span style="color:var(--text-dim);font-size:.7em">via astrometry.net hint</span>':'';html+='<div class="solver-section"><div class="solver-name">ASTAP <span class="badge '+(t.solved?'solved">SOLVED'+ts:'failed">FAILED'+ts)+'</span>'+ch+'</div>';if(t.solved)html+='<div class="result-grid">'+row('Solution',t.position)+'</div>';html+='</div>'}if(data.objects&&data.objects.length){html+='<div class="objects-section"><div class="objects-title">Objects in Field</div>';data.objects.forEach(o=>{html+='<span class="object-tag">'+esc(o.name)+'</span>'});html+='</div>'}if(data.total_time)html+='<div style="text-align:center;color:var(--text-dim);margin-top:8px;font-size:.85em">Total: '+data.total_time+'</div>';html+='<button class="toggle-raw" onclick="toggleRaw()">Show Raw Output</button><div class="raw-output" id="rawOutput">'+esc(data.raw_output||'')+'</div>';const r=document.getElementById('results');r.innerHTML=html;r.classList.add('active')}
function showSpinner(msg){document.getElementById('spinner').classList.add('active');document.getElementById('spinnerText').textContent=msg;document.getElementById('results').classList.remove('active');document.getElementById('errorMsg').classList.remove('active')}
function hideSpinner(){document.getElementById('spinner').classList.remove('active')}
function showError(msg){const e=document.getElementById('errorMsg');e.textContent=msg;e.classList.add('active')}
function row(l,v){return'<div class="result-label">'+l+'</div><div class="result-value">'+esc(v||'N/A')+'</div>'}
function esc(t){return(t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function toggleRaw(){const e=document.getElementById('rawOutput');e.style.display=e.style.display==='none'?'block':'none'}
</script></body></html>''' % _target_list_js

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('/opt/astro-discovery/certs/cert.pem', '/opt/astro-discovery/certs/key.pem'))
