#!/usr/bin/env python3
"""
🌐 PaniniFS Demo Server

Serveur web simple pour démontrer la décomposition/reconstruction de fichiers binaires
basée sur des grammaires universelles.

Features:
- Upload de fichiers PNG
- Décomposition en temps réel
- Visualisation des patterns universels (avec couleurs)
- Reconstruction et validation bit-perfect
- Export de la grammaire

Port: 5000
URL: http://localhost:5000
"""

from flask import Flask, request, render_template_string, jsonify, send_file
from pathlib import Path
import json
import io
import sys

# Importer nos modules
sys.path.insert(0, str(Path(__file__).parent))
from generic_decomposer import GenericDecomposer
from generic_reconstructor import GenericReconstructor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Dossier temporaire pour les uploads
UPLOAD_FOLDER = Path('./uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

GRAMMAR_FOLDER = Path('./format_grammars')


# ============================================================================
# HTML INTERFACE
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔬 PaniniFS Demo - Universal Binary Decomposer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-zone:hover {
            border-color: #764ba2;
            background: #f8f9ff;
        }
        .upload-zone.dragging {
            background: #e3e8ff;
            border-color: #5a67d8;
        }
        input[type="file"] { display: none; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:active { transform: translateY(0); }
        #results { display: none; }
        .pattern-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            margin: 3px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .pattern-structural { background: #e3f2fd; color: #1565c0; }
        .pattern-composition { background: #f3e5f5; color: #6a1b9a; }
        .pattern-validation { background: #e8f5e9; color: #2e7d32; }
        .chunk-item {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .success { color: #2e7d32; font-weight: bold; }
        .error { color: #c62828; font-weight: bold; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        code { 
            background: #2d3748;
            color: #68d391;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        .json-viewer {
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 PaniniFS Demo</h1>
        <p class="subtitle">Universal Binary Decomposer - Proof of Concept</p>
        
        <div class="card">
            <h2>📤 Upload Binary File</h2>
            <p style="margin-bottom: 20px; color: #666;">
                Upload a PNG file to see it decomposed into universal patterns
            </p>
            <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
                <p style="font-size: 3em; margin-bottom: 10px;">📁</p>
                <p style="font-size: 1.2em; margin-bottom: 5px;">Drop PNG file here or click to browse</p>
                <p style="color: #999; font-size: 0.9em;">Max 10MB</p>
            </div>
            <input type="file" id="fileInput" accept=".png" />
        </div>
        
        <div id="results">
            <div class="card">
                <h2>📊 Decomposition Results</h2>
                <div id="decompositionStats"></div>
                <div id="patternsUsed"></div>
                <div id="chunksDetails"></div>
            </div>
            
            <div class="card">
                <h2>🔧 Reconstruction Test</h2>
                <div id="reconstructionResults"></div>
            </div>
            
            <div class="card">
                <h2>💾 Export</h2>
                <button class="btn" onclick="downloadDecomposition()">📥 Download Decomposition JSON</button>
                <button class="btn" onclick="downloadReconstruction()">📥 Download Reconstructed File</button>
                <button class="btn" onclick="downloadGrammar()">📥 Download Grammar</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentDecomposition = null;
        let currentFilename = null;
        
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        // Drag & Drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragging'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragging'), false);
        });
        
        dropZone.addEventListener('drop', handleDrop, false);
        fileInput.addEventListener('change', handleFileSelect, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }
        
        function handleFileSelect(e) {
            handleFiles(e.target.files);
        }
        
        async function handleFiles(files) {
            if (files.length === 0) return;
            
            const file = files[0];
            currentFilename = file.name;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/decompose', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentDecomposition = data.decomposition;
                    displayResults(data);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Upload error: ' + error);
            }
        }
        
        function displayResults(data) {
            const decomp = data.decomposition;
            const stats = data.stats;
            const recon = data.reconstruction;
            
            // Stats
            document.getElementById('decompositionStats').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-value">${decomp.format}</div>
                        <div class="stat-label">Format</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${decomp.file_size}</div>
                        <div class="stat-label">Bytes</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${stats.total_elements}</div>
                        <div class="stat-label">Elements</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${Object.keys(stats.patterns_used).length}</div>
                        <div class="stat-label">Patterns</div>
                    </div>
                </div>
            `;
            
            // Patterns
            let patternsHTML = '<h3 style="margin-top: 20px;">🧩 Universal Patterns Used:</h3><div>';
            for (const [pattern, count] of Object.entries(stats.patterns_used)) {
                const category = getPatternCategory(pattern);
                patternsHTML += `<span class="pattern-badge pattern-${category}">${pattern} (${count}x)</span>`;
            }
            patternsHTML += '</div>';
            document.getElementById('patternsUsed').innerHTML = patternsHTML;
            
            // Reconstruction
            document.getElementById('reconstructionResults').innerHTML = `
                <p><strong>Reconstruction Status:</strong> <span class="${recon.bit_perfect ? 'success' : 'error'}">${recon.bit_perfect ? '✓ BIT-PERFECT' : '✗ FAILED'}</span></p>
                <p><strong>Original Size:</strong> ${recon.original_size} bytes</p>
                <p><strong>Reconstructed Size:</strong> ${recon.reconstructed_size} bytes</p>
                <p><strong>Size Match:</strong> ${recon.size_match ? '✓' : '✗'}</p>
            `;
            
            document.getElementById('results').style.display = 'block';
        }
        
        function getPatternCategory(pattern) {
            if (['MAGIC_NUMBER', 'LENGTH_PREFIXED_DATA'].includes(pattern)) return 'structural';
            if (['TYPED_CHUNK', 'SEQUENTIAL_STRUCTURE'].includes(pattern)) return 'composition';
            if (['CRC_CHECKSUM'].includes(pattern)) return 'validation';
            return 'structural';
        }
        
        function downloadDecomposition() {
            const blob = new Blob([JSON.stringify(currentDecomposition, null, 2)], { type: 'application/json' });
            downloadBlob(blob, 'decomposition_' + currentFilename + '.json');
        }
        
        async function downloadReconstruction() {
            const response = await fetch('/download_reconstruction');
            const blob = await response.blob();
            downloadBlob(blob, 'reconstructed_' + currentFilename);
        }
        
        async function downloadGrammar() {
            const response = await fetch('/download_grammar');
            const blob = await response.blob();
            downloadBlob(blob, 'grammar_png.json');
        }
        
        function downloadBlob(blob, filename) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Page principale"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/decompose', methods=['POST'])
def decompose():
    """Décompose un fichier binaire uploaded"""
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'})
    
    try:
        # Sauvegarder le fichier
        filepath = UPLOAD_FOLDER / file.filename
        file.save(str(filepath))
        
        # Décomposer
        grammar_file = GRAMMAR_FOLDER / 'png.json'
        decomposer = GenericDecomposer(filepath, grammar_file)
        decomposition = decomposer.decompose()
        
        # Valider
        from generic_decomposer import validate_decomposition
        stats = validate_decomposition(decomposition)
        
        # Reconstruire
        decomp_file = UPLOAD_FOLDER / f'decomp_{file.filename}.json'
        decomp_file.write_text(json.dumps(decomposition, indent=2))
        
        reconstructor = GenericReconstructor(decomp_file, grammar_file)
        reconstructed_data = reconstructor.reconstruct()
        
        recon_file = UPLOAD_FOLDER / f'recon_{file.filename}'
        recon_file.write_bytes(reconstructed_data)
        
        # Valider reconstruction
        from generic_reconstructor import validate_reconstruction
        validation = validate_reconstruction(filepath, recon_file)
        
        # Sauvegarder pour download
        app.config['LAST_DECOMPOSITION'] = decomp_file
        app.config['LAST_RECONSTRUCTION'] = recon_file
        app.config['LAST_GRAMMAR'] = grammar_file
        
        return jsonify({
            'success': True,
            'decomposition': decomposition,
            'stats': stats,
            'reconstruction': validation
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/download_reconstruction')
def download_reconstruction():
    """Télécharge le fichier reconstruit"""
    filepath = app.config.get('LAST_RECONSTRUCTION')
    if filepath and filepath.exists():
        return send_file(str(filepath), as_attachment=True)
    return "No file available", 404


@app.route('/download_grammar')
def download_grammar():
    """Télécharge la grammaire"""
    filepath = app.config.get('LAST_GRAMMAR')
    if filepath and filepath.exists():
        return send_file(str(filepath), as_attachment=True)
    return "No file available", 404


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🌐 PaniniFS Demo Server")
    print("=" * 70)
    print(f"\n🚀 Server starting on http://localhost:5000")
    print(f"📁 Upload folder: {UPLOAD_FOLDER.absolute()}")
    print(f"📚 Grammar folder: {GRAMMAR_FOLDER.absolute()}")
    print("\n💡 Open http://localhost:5000 in your browser")
    print("\n" + "=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
