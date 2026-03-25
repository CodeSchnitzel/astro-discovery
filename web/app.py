#!/usr/bin/env python3
"""StarFinder Web UI - Plate Solving Server for field use."""

import os
import re
import subprocess
import uuid
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max upload
UPLOAD_DIR = '/tmp/starfinder-uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'nef', 'cr2', 'arw', 'fits', 'fit', 'jpg', 'jpeg',
                      'tiff', 'tif', 'png'}

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>StarFinder</title>
<style>
  :root {
    --bg: #0a0000;
    --surface: #1a0505;
    --border: #3a1515;
    --red: #8b2020;
    --red-bright: #cc3333;
    --red-dim: #551111;
    --text: #cc8888;
    --text-bright: #eecccc;
    --text-dim: #775555;
    --success: #338833;
    --success-text: #88cc88;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, system-ui, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 16px;
  }
  h1 {
    text-align: center;
    color: var(--red-bright);
    font-size: 1.5em;
    margin-bottom: 4px;
    letter-spacing: 2px;
  }
  .subtitle {
    text-align: center;
    color: var(--text-dim);
    font-size: 0.85em;
    margin-bottom: 20px;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .dropzone {
    border: 2px dashed var(--red);
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .dropzone.dragover {
    border-color: var(--red-bright);
    background: var(--red-dim);
  }
  .dropzone.has-file {
    border-color: var(--success);
    border-style: solid;
  }
  .dropzone-icon { font-size: 2.5em; margin-bottom: 8px; }
  .dropzone-text { color: var(--text); font-size: 1.1em; }
  .dropzone-hint { color: var(--text-dim); font-size: 0.8em; margin-top: 6px; }
  .filename {
    color: var(--text-bright);
    font-weight: bold;
    font-size: 1.1em;
    word-break: break-all;
  }
  .filesize { color: var(--text-dim); font-size: 0.85em; margin-top: 4px; }
  #fileInput { display: none; }

  .options { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
  .options label {
    display: block;
    color: var(--text-dim);
    font-size: 0.8em;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .options input {
    width: 100%;
    padding: 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-bright);
    font-size: 1em;
    text-align: center;
  }
  .options input::placeholder { color: var(--text-dim); }
  .options input:focus {
    outline: none;
    border-color: var(--red);
  }

  .solve-btn {
    display: block;
    width: 100%;
    padding: 16px;
    background: var(--red);
    color: var(--text-bright);
    border: none;
    border-radius: 12px;
    font-size: 1.2em;
    font-weight: bold;
    cursor: pointer;
    letter-spacing: 1px;
    transition: all 0.2s;
  }
  .solve-btn:hover { background: var(--red-bright); }
  .solve-btn:disabled {
    background: var(--red-dim);
    color: var(--text-dim);
    cursor: not-allowed;
  }

  .spinner {
    display: none;
    text-align: center;
    padding: 30px;
  }
  .spinner.active { display: block; }
  .spinner-dot {
    display: inline-block;
    width: 12px; height: 12px;
    background: var(--red-bright);
    border-radius: 50%;
    margin: 0 4px;
    animation: pulse 1.4s infinite ease-in-out;
  }
  .spinner-dot:nth-child(2) { animation-delay: 0.2s; }
  .spinner-dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes pulse {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1); opacity: 1; }
  }
  .spinner-text {
    color: var(--text-dim);
    margin-top: 12px;
    font-size: 0.9em;
  }

  .results { display: none; }
  .results.active { display: block; }
  .result-header {
    color: var(--red-bright);
    font-size: 1.1em;
    font-weight: bold;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }
  .result-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 6px 16px;
    margin-bottom: 16px;
  }
  .result-label {
    color: var(--text-dim);
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 4px 0;
  }
  .result-value {
    color: var(--text-bright);
    font-family: 'SF Mono', 'Consolas', monospace;
    font-size: 1.05em;
    padding: 4px 0;
  }
  .result-value.solved { color: var(--success-text); }
  .result-value.failed { color: var(--red-bright); }

  .solver-section { margin-bottom: 20px; }
  .solver-name {
    color: var(--text);
    font-weight: bold;
    font-size: 0.95em;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: bold;
    text-transform: uppercase;
  }
  .badge.solved { background: var(--success); color: #fff; }
  .badge.failed { background: var(--red-dim); color: var(--red-bright); }

  .raw-output {
    margin-top: 12px;
    padding: 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-family: monospace;
    font-size: 0.75em;
    color: var(--text-dim);
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 200px;
    overflow-y: auto;
    display: none;
  }
  .toggle-raw {
    background: none;
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.8em;
    cursor: pointer;
    margin-top: 8px;
  }
  .toggle-raw:hover { border-color: var(--red); color: var(--text); }

  .error-msg {
    display: none;
    background: var(--red-dim);
    border: 1px solid var(--red);
    border-radius: 8px;
    padding: 12px;
    color: var(--red-bright);
    text-align: center;
  }
  .error-msg.active { display: block; }
</style>
</head>
<body>

<h1>STARFINDER</h1>
<p class="subtitle">Plate Solving Station</p>

<div class="card">
  <div class="dropzone" id="dropzone">
    <div class="dropzone-icon" id="dzIcon">&#9733;</div>
    <div class="dropzone-text" id="dzText">Tap to select or drop image here</div>
    <div class="dropzone-hint" id="dzHint">NEF &bull; CR2 &bull; FITS &bull; JPG &bull; TIFF &bull; PNG</div>
  </div>
  <input type="file" id="fileInput" accept=".nef,.cr2,.arw,.fits,.fit,.jpg,.jpeg,.tiff,.tif,.png">
</div>

<div class="card">
  <div class="options">
    <div>
      <label>FOV (&deg;)</label>
      <input type="number" id="fov" value="4.55" step="0.01" min="0.1" max="180" placeholder="4.55">
    </div>
    <div>
      <label>RA (hrs)</label>
      <input type="number" id="ra" step="0.1" min="0" max="24" placeholder="optional">
    </div>
    <div>
      <label>Dec (&deg;)</label>
      <input type="number" id="dec" step="0.1" min="-90" max="90" placeholder="optional">
    </div>
  </div>
</div>

<button class="solve-btn" id="solveBtn" disabled>SOLVE</button>

<div class="spinner" id="spinner">
  <div>
    <span class="spinner-dot"></span>
    <span class="spinner-dot"></span>
    <span class="spinner-dot"></span>
  </div>
  <div class="spinner-text" id="spinnerText">Uploading image...</div>
</div>

<div class="error-msg" id="errorMsg"></div>

<div class="results card" id="results"></div>

<script>
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const solveBtn = document.getElementById('solveBtn');
const spinner = document.getElementById('spinner');
const spinnerText = document.getElementById('spinnerText');
const errorMsg = document.getElementById('errorMsg');
const resultsDiv = document.getElementById('results');
let selectedFile = null;

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) selectFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files.length) selectFile(fileInput.files[0]); });

function selectFile(file) {
    selectedFile = file;
    dropzone.classList.add('has-file');
    document.getElementById('dzIcon').textContent = '\u2713';
    document.getElementById('dzText').innerHTML = '<span class="filename">' + file.name + '</span>';
    const mb = (file.size / 1024 / 1024).toFixed(1);
    document.getElementById('dzHint').innerHTML = '<span class="filesize">' + mb + ' MB</span>';
    solveBtn.disabled = false;
    resultsDiv.classList.remove('active');
    errorMsg.classList.remove('active');
}

function resetDropzone() {
    selectedFile = null;
    dropzone.classList.remove('has-file');
    document.getElementById('dzIcon').innerHTML = '&#9733;';
    document.getElementById('dzText').textContent = 'Tap to select or drop image here';
    document.getElementById('dzHint').innerHTML = 'NEF &bull; CR2 &bull; FITS &bull; JPG &bull; TIFF &bull; PNG';
    solveBtn.disabled = true;
}

solveBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    solveBtn.disabled = true;
    spinner.classList.add('active');
    spinnerText.textContent = 'Uploading image...';
    resultsDiv.classList.remove('active');
    errorMsg.classList.remove('active');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('fov', document.getElementById('fov').value || '4.55');
    const ra = document.getElementById('ra').value;
    const dec = document.getElementById('dec').value;
    if (ra) formData.append('ra', ra);
    if (dec) formData.append('dec', dec);

    try {
        spinnerText.textContent = 'Solving... this may take up to a few minutes';
        const resp = await fetch('/solve', { method: 'POST', body: formData });
        const data = await resp.json();
        spinner.classList.remove('active');

        if (data.error) {
            errorMsg.textContent = data.error;
            errorMsg.classList.add('active');
            solveBtn.disabled = false;
            return;
        }
        showResults(data);
    } catch (err) {
        spinner.classList.remove('active');
        errorMsg.textContent = 'Connection error: ' + err.message;
        errorMsg.classList.add('active');
    }
    solveBtn.disabled = false;
});

function showResults(data) {
    let html = '<div class="result-header">Results: ' + data.filename + '</div>';

    if (data.astrometry) {
        const a = data.astrometry;
        const solved = a.solved;
        const timeStr = a.solve_time ? ' (' + a.solve_time + ')' : '';
        html += '<div class="solver-section">';
        html += '<div class="solver-name">Astrometry.net <span class="badge ' +
                (solved ? 'solved">SOLVED' + timeStr : 'failed">FAILED' + timeStr) + '</span></div>';
        if (solved) {
            html += '<div class="result-grid">';
            html += row('Center RA', a.ra);
            html += row('Center Dec', a.dec);
            html += row('Scale', a.scale);
            html += row('Field of View', a.fov);
            html += '</div>';
        }
        html += '</div>';
    }

    if (data.astap) {
        const t = data.astap;
        const solved = t.solved;
        const timeStr = t.solve_time ? ' (' + t.solve_time + ')' : '';
        const chainedStr = t.chained ? ' <span style="color:var(--text-dim);font-size:0.75em">via astrometry.net hint</span>' : '';
        html += '<div class="solver-section">';
        html += '<div class="solver-name">ASTAP <span class="badge ' +
                (solved ? 'solved">SOLVED' + timeStr : 'failed">FAILED' + timeStr) + '</span>' + chainedStr + '</div>';
        if (solved) {
            html += '<div class="result-grid">';
            html += row('Solution', t.position);
            if (t.fov_warning) html += row('Note', t.fov_warning);
            html += '</div>';
        }
        html += '</div>';
    }

    // Total time
    if (data.total_time) {
        html += '<div style="text-align:center;color:var(--text-dim);margin-top:8px;font-size:0.85em">Total: ' + data.total_time + '</div>';
    }

    html += '<button class="toggle-raw" onclick="toggleRaw()">Show Raw Output</button>';
    html += '<div class="raw-output" id="rawOutput">' + escapeHtml(data.raw_output || '') + '</div>';

    resultsDiv.innerHTML = html;
    resultsDiv.classList.add('active');
    resetDropzone();
}

function row(label, value) {
    return '<div class="result-label">' + label + '</div><div class="result-value">' + escapeHtml(value || 'N/A') + '</div>';
}
function escapeHtml(t) {
    return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function toggleRaw() {
    const el = document.getElementById('rawOutput');
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}
</script>
</body>
</html>'''


def parse_astrometry_output(text):
    """Parse astrometry.net output from platesolve."""
    result = {'solved': False}
    if '[+] SOLVED!' in text:
        result['solved'] = True
        # Extract solve time from "[+] SOLVED!  (12345ms)"
        m = re.search(r'\[\+\] SOLVED!\s*\((\d+)ms\)', text)
        if m:
            ms = int(m.group(1))
            result['solve_time'] = '%.1fs' % (ms / 1000.0)
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('Center RA:'):
                result['ra'] = line.split(':', 1)[1].strip()
            elif line.startswith('Center Dec:'):
                result['dec'] = line.split(':', 1)[1].strip()
            elif line.startswith('Scale:'):
                result['scale'] = line.split(':', 1)[1].strip()
            elif line.startswith('FOV:'):
                result['fov'] = line.split(':', 1)[1].strip()
    else:
        # Extract time from failed solve "[-] Failed to solve  (12345ms)"
        m = re.search(r'\[\-\] Failed to solve\s*\((\d+)ms\)', text)
        if m:
            ms = int(m.group(1))
            result['solve_time'] = '%.1fs' % (ms / 1000.0)
    return result


def parse_astap_output(text):
    """Parse ASTAP output from platesolve."""
    result = {'solved': False}
    for line in text.split('\n'):
        line = line.strip()
        if 'PLTSOLVD=T' in line:
            result['solved'] = True
        m = re.search(r'Solution found:\s*(.+)', line)
        if m:
            result['position'] = m.group(1).strip()
        m = re.search(r'Solved in (.+?)\.', line)
        if m:
            result['time'] = m.group(1).strip()
        if line.startswith('Warning'):
            result['fov_warning'] = line
        # Extract timing from "[+] ASTAP result:  (1234ms)" or "[-] ASTAP failed  (1234ms)"
        m2 = re.search(r'\((\d+)ms\)', line)
        if m2 and ('ASTAP result' in line or 'ASTAP failed' in line):
            ms = int(m2.group(1))
            result['solve_time'] = '%.1fs' % (ms / 1000.0)

    # Also look for chaining hint
    if 'Using Astrometry.net solution as hint' in text:
        result['chained'] = True
    return result


@app.route('/')
def index():
    return render_template_string(HTML_PAGE)


@app.route('/solve', methods=['POST'])
def solve():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No file selected'}), 400

    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported format: .{ext}'}), 400

    # Save uploaded file
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    filepath = os.path.join(job_dir, f.filename)
    f.save(filepath)

    # Build platesolve command
    fov = request.form.get('fov', '4.55')
    cmd = ['platesolve', filepath, '--fov', fov]

    ra = request.form.get('ra', '').strip()
    dec = request.form.get('dec', '').strip()
    if ra:
        cmd.extend(['--ra', ra])
    if dec:
        cmd.extend(['--dec', dec])

    # Run solver
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600
        )
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Solve timed out after 10 minutes'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Split output into astrometry and astap sections
    astro_text = ''
    astap_text = ''
    sections = re.split(r'={3,}', output)
    for i, section in enumerate(sections):
        if 'ASTROMETRY' in section and not astro_text and i + 1 < len(sections):
            astro_text = sections[i + 1]
        elif 'ASTAP' in section and not astap_text and i + 1 < len(sections):
            astap_text = sections[i + 1]

    # Extract total time from output
    total_time = ''
    m = re.search(r'Total time:\s*(\S+)', output)
    if m:
        total_time = m.group(1)

    result = {
        'filename': f.filename,
        'astrometry': parse_astrometry_output(astro_text),
        'astap': parse_astap_output(astap_text),
        'total_time': total_time,
        'raw_output': output
    }

    # Cleanup uploaded files
    try:
        import shutil
        shutil.rmtree(job_dir, ignore_errors=True)
    except Exception:
        pass

    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
