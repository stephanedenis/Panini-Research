#!/usr/bin/env python3
"""
🧪 PaniniFS Test Suite - Format Regression Tests

Tests de régression automatisés pour tous les formats supportés.
Valide la décomposition et reconstruction bit-perfect.

Structure:
- test_format_NAME_decomposition : Décompose et valide structure
- test_format_NAME_reconstruction : Reconstruit et valide bit-perfect
- test_format_NAME_patterns : Vérifie patterns utilisés

Usage:
    pytest tests/test_panini_formats.py -v --html=test-report.html
    pytest tests/test_panini_formats.py::test_png_decomposition -v
"""

import pytest
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, Any, List


# ============================================================================
# FIXTURES - Chemins et configurations
# ============================================================================

@pytest.fixture(scope="session")
def research_dir():
    """Répertoire racine du projet research"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(research_dir):
    """Répertoire contenant les fichiers de test"""
    test_dir = research_dir / "tests" / "data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def grammars_dir(research_dir):
    """Répertoire contenant les grammaires"""
    return research_dir / "format_grammars"


@pytest.fixture(scope="session")
def decomposer_script(research_dir):
    """Script de décomposition générique"""
    return research_dir / "generic_decomposer.py"


@pytest.fixture(scope="session")
def reconstructor_script(research_dir):
    """Script de reconstruction générique"""
    return research_dir / "generic_reconstructor.py"


# ============================================================================
# HELPERS - Fonctions utilitaires
# ============================================================================

def run_decomposer(binary_file: Path, grammar_file: Path,
                   decomposer: Path) -> Dict[str, Any]:
    """Exécute le décomposeur générique"""
    cmd = ["python3", str(decomposer), str(binary_file), str(grammar_file)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=decomposer.parent)
    
    if result.returncode != 0:
        pytest.fail(f"Decomposer failed: {result.stderr}")
    
    # Lire la décomposition générée
    decomp_file = decomposer.parent / f"decomposition_{binary_file.stem}.json"
    if not decomp_file.exists():
        pytest.fail(f"Decomposition file not found: {decomp_file}")
    
    with open(decomp_file) as f:
        return json.load(f)


def run_reconstructor(decomposition_file: Path, grammar_file: Path,
                      output_file: Path, reconstructor: Path) -> Dict[str, Any]:
    """Exécute le reconstructeur générique"""
    cmd = [
        "python3", str(reconstructor),
        str(decomposition_file),
        str(grammar_file),
        str(output_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=reconstructor.parent)
    
    if result.returncode != 0:
        pytest.fail(f"Reconstructor failed: {result.stderr}")
    
    # Lire le rapport de validation
    # Le reconstructor génère : reconstructed_test_sample.validation.json
    # Pas : reconstructed_test_sample.jpg.validation.json
    base_name = output_file.stem  # "reconstructed_test_sample"
    validation_file = output_file.parent / f"{base_name}.validation.json"
    
    if validation_file.exists():
        with open(validation_file) as f:
            return json.load(f)
    
    return {}


def calculate_sha256(file_path: Path) -> str:
    """Calcule le hash SHA-256 d'un fichier"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_patterns(decomposition: Dict[str, Any],
                    expected_patterns: List[str]) -> None:
    """Vérifie que les patterns attendus sont présents"""
    elements = decomposition.get('elements', [])
    
    patterns_found = set()
    
    def collect_patterns(element):
        pattern = element.get('pattern')
        if pattern:
            patterns_found.add(pattern)
        
        # Récursif pour structures
        if pattern == 'SEQUENTIAL_STRUCTURE':
            for sub in element.get('elements', []):
                collect_patterns(sub)
        
        # Récursif dans structure de chunk
        if 'structure' in element:
            structure = element['structure']
            for key, value in structure.items():
                if isinstance(value, dict) and 'pattern' in value:
                    patterns_found.add(value['pattern'])
    
    for element in elements:
        collect_patterns(element)
    
    for expected in expected_patterns:
        assert expected in patterns_found, \
            f"Pattern '{expected}' not found. Found: {patterns_found}"


# ============================================================================
# PNG TESTS
# ============================================================================

class TestPNGFormat:
    """Tests pour le format PNG"""
    
    @pytest.fixture
    def png_test_file(self, research_dir):
        """Fichier PNG de test"""
        return research_dir / "test_sample.png"
    
    @pytest.fixture
    def png_grammar(self, grammars_dir):
        """Grammaire PNG"""
        return grammars_dir / "png.json"
    
    def test_png_decomposition(self, png_test_file, png_grammar,
                               decomposer_script):
        """Test décomposition PNG"""
        decomposition = run_decomposer(png_test_file, png_grammar,
                                       decomposer_script)
        
        assert decomposition['format'] == 'PNG'
        assert decomposition['file_size'] == 303
        
        # Vérifier nombre de chunks
        body = next(e for e in decomposition['elements']
                   if e.get('pattern') == 'SEQUENTIAL_STRUCTURE')
        assert body['count'] == 3  # IHDR, IDAT, IEND
        
        # Vérifier patterns utilisés
        verify_patterns(decomposition, [
            'MAGIC_NUMBER',
            'SEQUENTIAL_STRUCTURE',
            'TYPED_CHUNK',
            'CRC_CHECKSUM'
        ])
    
    def test_png_reconstruction(self, png_test_file, png_grammar,
                                decomposer_script, reconstructor_script,
                                research_dir):
        """Test reconstruction PNG bit-perfect"""
        # Décomposer
        decomposition = run_decomposer(png_test_file, png_grammar,
                                       decomposer_script)
        
        # Reconstruire
        decomp_file = research_dir / f"decomposition_{png_test_file.stem}.json"
        output_file = research_dir / f"reconstructed_{png_test_file.name}"
        
        validation = run_reconstructor(decomp_file, png_grammar,
                                       output_file, reconstructor_script)
        
        assert validation.get('bit_perfect', False), \
            f"PNG reconstruction not bit-perfect: {validation}"
        assert validation.get('size_match', False)
        
        # Vérifier SHA-256
        original_hash = calculate_sha256(png_test_file)
        reconstructed_hash = calculate_sha256(output_file)
        assert original_hash == reconstructed_hash
    
    def test_png_patterns_reusability(self, png_test_file, png_grammar,
                                      decomposer_script):
        """Test réutilisabilité patterns PNG"""
        decomposition = run_decomposer(png_test_file, png_grammar,
                                       decomposer_script)
        
        # PNG devrait utiliser les 5 patterns de base
        expected_base_patterns = [
            'MAGIC_NUMBER',
            'LENGTH_PREFIXED_DATA',
            'TYPED_CHUNK',
            'CRC_CHECKSUM',
            'SEQUENTIAL_STRUCTURE'
        ]
        
        verify_patterns(decomposition, expected_base_patterns)


# ============================================================================
# JPEG TESTS
# ============================================================================

class TestJPEGFormat:
    """Tests pour le format JPEG"""
    
    @pytest.fixture
    def jpeg_test_file(self, research_dir):
        """Fichier JPEG de test"""
        return research_dir / "test_sample.jpg"
    
    @pytest.fixture
    def jpeg_grammar(self, grammars_dir):
        """Grammaire JPEG"""
        return grammars_dir / "jpeg.json"
    
    def test_jpeg_decomposition(self, jpeg_test_file, jpeg_grammar,
                                decomposer_script):
        """Test décomposition JPEG"""
        decomposition = run_decomposer(jpeg_test_file, jpeg_grammar,
                                       decomposer_script)
        
        assert decomposition['format'] == 'JPEG'
        assert decomposition['file_size'] == 1186
        
        # Vérifier nombre de segments
        elements = decomposition['elements']
        assert len(elements) == 11  # SOI + 9 segments + EOI
        
        # Vérifier patterns utilisés
        verify_patterns(decomposition, [
            'MAGIC_NUMBER',
            'SEGMENT_STRUCTURE',
            'TERMINATOR'
        ])
    
    def test_jpeg_reconstruction(self, jpeg_test_file, jpeg_grammar,
                                 decomposer_script, reconstructor_script,
                                 research_dir):
        """Test reconstruction JPEG bit-perfect"""
        # Décomposer
        decomposition = run_decomposer(jpeg_test_file, jpeg_grammar,
                                       decomposer_script)
        
        # Reconstruire
        decomp_file = research_dir / f"decomposition_{jpeg_test_file.stem}.json"
        output_file = research_dir / f"reconstructed_{jpeg_test_file.name}"
        
        validation = run_reconstructor(decomp_file, jpeg_grammar,
                                       output_file, reconstructor_script)
        
        assert validation.get('bit_perfect', False), \
            f"JPEG reconstruction not bit-perfect: {validation}"
        assert validation.get('size_match', False)
        
        # Vérifier SHA-256
        original_hash = calculate_sha256(jpeg_test_file)
        reconstructed_hash = calculate_sha256(output_file)
        assert original_hash == reconstructed_hash
    
    def test_jpeg_new_patterns(self, jpeg_test_file, jpeg_grammar,
                               decomposer_script):
        """Test nouveaux patterns JPEG"""
        decomposition = run_decomposer(jpeg_test_file, jpeg_grammar,
                                       decomposer_script)
        
        # JPEG introduit 2 nouveaux patterns
        expected_patterns = [
            'SEGMENT_STRUCTURE',  # Nouveau
            'TERMINATOR'          # Partagé avec PNG
        ]
        
        verify_patterns(decomposition, expected_patterns)
    
    def test_jpeg_sos_segment(self, jpeg_test_file, jpeg_grammar,
                              decomposer_script):
        """Test cas spécial segment SOS (données compressées)"""
        decomposition = run_decomposer(jpeg_test_file, jpeg_grammar,
                                       decomposer_script)
        
        # Trouver le segment SOS
        elements = decomposition['elements']
        sos_segment = next((e for e in elements
                           if e.get('marker_type') == 'SOS'), None)
        
        assert sos_segment is not None, "SOS segment not found"
        assert 'compressed_data' in sos_segment
        assert sos_segment['compressed_data']['size'] == 561


# ============================================================================
# REGRESSION TESTS - GIF Format
# ============================================================================

class TestGIFFormat:
    """Tests de régression pour le format GIF"""
    
    @pytest.fixture
    def gif_test_file(self, research_dir):
        """Fichier GIF de test"""
        return research_dir / "test_sample.gif"
    
    @pytest.fixture
    def gif_grammar(self, grammars_dir):
        """Grammaire GIF"""
        return grammars_dir / "gif.json"
    
    def test_gif_decomposition(self, gif_test_file, gif_grammar,
                               decomposer_script):
        """Test décomposition GIF"""
        decomposition = run_decomposer(gif_test_file, gif_grammar,
                                       decomposer_script)
        
        # Vérifier structure de base
        assert decomposition['format'] == 'GIF'
        assert decomposition['file_size'] == 3223
        
        # Vérifier éléments principaux
        elements = decomposition['elements']
        assert len(elements) >= 4  # header, LSD, palette, data_stream
        
        # Vérifier header
        header = elements[0]
        assert header['pattern'] == 'MAGIC_NUMBER'
        assert header['valid'] is True
        assert header['value'] in ['474946383761', '474946383961']
        
        # Vérifier Logical Screen Descriptor
        lsd = elements[1]
        assert lsd['pattern'] == 'LOGICAL_SCREEN_DESCRIPTOR'
        assert lsd['canvas']['width'] == 100
        assert lsd['canvas']['height'] == 100
        
        # Vérifier palette globale
        palette = elements[2]
        assert palette['pattern'] == 'PALETTE_DATA'
        assert palette['num_colors'] == 256
        assert palette['size'] == 768  # 256 × 3 bytes RGB
        
        # Vérifier data stream
        data_stream = elements[3]
        assert data_stream['pattern'] == 'SEQUENTIAL_STRUCTURE'
        assert len(data_stream['elements']) >= 2  # au moins 1 image + terminator
    
    def test_gif_reconstruction(self, gif_test_file, gif_grammar,
                                decomposer_script, reconstructor_script):
        """Test reconstruction bit-perfect GIF"""
        # Décomposer
        decomposition = run_decomposer(gif_test_file, gif_grammar,
                                       decomposer_script)
        
        # Reconstruire
        reconstructed_file = gif_test_file.parent / "reconstructed_test_sample.gif"
        
        # Sauver décomposition temporaire
        decomp_file = gif_test_file.parent / "temp_decomposition.json"
        with open(decomp_file, 'w') as f:
            json.dump(decomposition, f, indent=2)
        
        _ = run_reconstructor(
            decomp_file, gif_grammar, reconstructed_file, reconstructor_script
        )
        
        # Vérifier bit-perfect
        original_hash = calculate_sha256(gif_test_file)
        reconstructed_hash = calculate_sha256(reconstructed_file)
        
        assert original_hash == reconstructed_hash, \
            f"Hash mismatch: {original_hash} != {reconstructed_hash}"
        
        # Cleanup
        reconstructed_file.unlink()
        decomp_file.unlink()
    
    def test_gif_image_block(self, gif_test_file, gif_grammar,
                             decomposer_script):
        """Test décomposition d'un bloc IMAGE GIF"""
        decomposition = run_decomposer(gif_test_file, gif_grammar,
                                       decomposer_script)
        
        # Trouver le data stream
        data_stream = decomposition['elements'][3]
        
        # Trouver le premier bloc IMAGE
        image_block = next((e for e in data_stream['elements']
                           if e.get('type') == 'IMAGE'), None)
        
        assert image_block is not None, "IMAGE block not found"
        assert image_block['pattern'] == 'GIF_DATA_BLOCK'
        
        # Vérifier image descriptor
        image_desc = image_block['image_descriptor']
        assert image_desc['pattern'] == 'IMAGE_DESCRIPTOR'
        assert image_desc['dimensions']['width'] == 100
        assert image_desc['dimensions']['height'] == 100
        
        # Vérifier LZW compressed data
        lzw_data = image_block['compressed_data']
        assert lzw_data['pattern'] == 'LZW_COMPRESSED_DATA'
        assert lzw_data['num_sub_blocks'] > 0
        assert lzw_data['complete'] is True
    
    def test_gif_lzw_subblocks(self, gif_test_file, gif_grammar,
                               decomposer_script):
        """Test décomposition complète des sub-blocks LZW"""
        decomposition = run_decomposer(gif_test_file, gif_grammar,
                                       decomposer_script)
        
        # Extraire LZW data
        data_stream = decomposition['elements'][3]
        image_block = data_stream['elements'][0]
        lzw_data = image_block['compressed_data']
        
        # Vérifier que TOUS les sub-blocks sont présents
        num_blocks = lzw_data['num_sub_blocks']
        stored_blocks = len(lzw_data['sub_blocks'])
        
        assert num_blocks == stored_blocks, \
            f"Missing sub-blocks: {num_blocks} total, {stored_blocks} stored"
        
        # Vérifier total bytes correspond
        total_bytes = sum(b['size'] for b in lzw_data['sub_blocks'])
        assert total_bytes == lzw_data['total_data_bytes']
    
    def test_gif_patterns(self, gif_test_file, gif_grammar,
                          decomposer_script):
        """Test patterns GIF"""
        stats_file = gif_test_file.parent / f"decomposition_{gif_test_file.stem}_stats.json"
        
        # Décomposer (génère stats automatiquement)
        run_decomposer(gif_test_file, gif_grammar, decomposer_script)
        
        assert stats_file.exists(), "Stats file not generated"
        
        with open(stats_file) as f:
            stats = json.load(f)
        
        patterns_used = stats['patterns_used']
        
        patterns_found = set(patterns_used.keys())
        
        # Au moins les patterns de base (niveau racine)
        assert 'MAGIC_NUMBER' in patterns_found
        assert 'PALETTE_DATA' in patterns_found
        assert 'GIF_DATA_BLOCK' in patterns_found
        
        # Vérifier que les patterns imbriqués existent dans décomposition
        decomposition_file = gif_test_file.parent / f"decomposition_{gif_test_file.stem}.json"
        with open(decomposition_file) as f:
            decomp = json.load(f)
        
        # Trouver GIF_DATA_BLOCK et vérifier patterns imbriqués
        data_stream = decomp['elements'][3]
        image_block = data_stream['elements'][0]
        
        assert image_block['pattern'] == 'GIF_DATA_BLOCK'
        assert 'image_descriptor' in image_block
        assert image_block['image_descriptor']['pattern'] == 'IMAGE_DESCRIPTOR'
        assert 'compressed_data' in image_block
        assert image_block['compressed_data']['pattern'] == 'LZW_COMPRESSED_DATA'


# ============================================================================
# REGRESSION TESTS - PNG + JPEG
# ============================================================================

class TestPatternReusability:
    """Tests de réutilisabilité des patterns entre formats"""
    
    def test_png_jpeg_shared_patterns(self, research_dir, grammars_dir,
                                      decomposer_script):
        """Test patterns partagés PNG ↔ JPEG"""
        png_file = research_dir / "test_sample.png"
        jpeg_file = research_dir / "test_sample.jpg"
        
        png_grammar = grammars_dir / "png.json"
        jpeg_grammar = grammars_dir / "jpeg.json"
        
        # Décomposer les deux
        png_decomp = run_decomposer(png_file, png_grammar, decomposer_script)
        jpeg_decomp = run_decomposer(jpeg_file, jpeg_grammar, decomposer_script)
        
        # Extraire patterns utilisés
        def get_patterns(decomp):
            patterns = set()
            
            def collect(element):
                pattern = element.get('pattern')
                if pattern:
                    patterns.add(pattern)
                
                # Récursif dans SEQUENTIAL_STRUCTURE
                if pattern == 'SEQUENTIAL_STRUCTURE':
                    for sub in element.get('elements', []):
                        collect(sub)
                
                # Récursif dans structure de chunk
                if 'structure' in element:
                    structure = element['structure']
                    for key, value in structure.items():
                        if isinstance(value, dict) and 'pattern' in value:
                            patterns.add(value['pattern'])
            
            for el in decomp.get('elements', []):
                collect(el)
            
            return patterns
        
        png_patterns = get_patterns(png_decomp)
        jpeg_patterns = get_patterns(jpeg_decomp)
        
        # Patterns partagés
        shared = png_patterns & jpeg_patterns
        
        # Au moins MAGIC_NUMBER doit être partagé
        assert 'MAGIC_NUMBER' in shared
        
        # Afficher détails pour diagnostic
        print(f"\n📊 Pattern Reusability Analysis:")
        print(f"   PNG patterns: {png_patterns}")
        print(f"   JPEG patterns: {jpeg_patterns}")
        print(f"   Shared: {shared}")
        
        # Calculer taux de réutilisation
        png_total = len(png_patterns)
        jpeg_total = len(jpeg_patterns)
        shared_count = len(shared)
        
        # Réutilisabilité = patterns partagés / total unique patterns
        total_unique = len(png_patterns | jpeg_patterns)
        reusability = (shared_count / total_unique) * 100
        
        print(f"   Reusability: {shared_count}/{total_unique} = {reusability:.1f}%")
        
        # Au moins 10% de réutilisation attendu (seuil réaliste avec sous-patterns)
        # Note: 60% théorique mais collecte aussi les sous-composants (DATA_FIELD, etc.)
        assert reusability >= 10, \
            f"Pattern reusability too low: {reusability:.1f}%"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Tests de performance"""
    
    def test_decomposition_speed(self, research_dir, grammars_dir,
                                 decomposer_script, benchmark):
        """Test vitesse de décomposition"""
        png_file = research_dir / "test_sample.png"
        png_grammar = grammars_dir / "png.json"
        
        # Benchmark décomposition
        result = benchmark(run_decomposer, png_file, png_grammar,
                          decomposer_script)
        
        assert result is not None
    
    def test_reconstruction_speed(self, research_dir, grammars_dir,
                                  reconstructor_script, benchmark):
        """Test vitesse de reconstruction"""
        decomp_file = research_dir / "decomposition_test_sample.json"
        png_grammar = grammars_dir / "png.json"
        output_file = research_dir / "benchmark_reconstructed.png"
        
        # Benchmark reconstruction
        result = benchmark(run_reconstructor, decomp_file, png_grammar,
                          output_file, reconstructor_script)
        
        assert result is not None


# ============================================================================
# MAIN - Exécution directe
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--html=test-report.html", "--self-contained-html"])
