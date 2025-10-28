#!/usr/bin/env python3
"""
Test Suite for Semantic Extractors
===================================
Validates semantic extraction from text-based formats.

Author: PaniniFS Research Team
Date: 2025-10-26
Version: v3.1-alpha
"""

import json
import pytest
from pathlib import Path
from semantic_extractor import (
    SVGSemanticExtractor,
    JSONSemanticExtractor,
    XMLSemanticExtractor,
    HTMLSemanticExtractor,
    create_extractor
)


class TestSVGSemanticExtractor:
    """Test SVG semantic extraction"""
    
    def test_svg_basic_shapes(self):
        """Test extraction of basic SVG shapes"""
        extractor = SVGSemanticExtractor()
        result = extractor.extract('test_sample.svg')
        
        assert result['format'] == 'SVG'
        assert result['semantic_extraction'] is True
        
        # Check extracted elements
        elements = result['elements']
        assert len(elements) == 3
        
        # Verify rectangle
        rect = next(e for e in elements if e['type'] == 'rectangle')
        assert rect['geometry']['position']['x'] == 10.0
        assert rect['geometry']['position']['y'] == 10.0
        assert rect['geometry']['size']['width'] == 80.0
        assert rect['geometry']['size']['height'] == 80.0
        assert rect['style']['fill'] == '#FF5733'
        assert rect['style']['stroke'] == '#000'
        assert rect['style']['stroke_width'] == 2.0
        
        # Verify circle
        circle = next(e for e in elements if e['type'] == 'circle')
        assert circle['geometry']['center']['x'] == 50.0
        assert circle['geometry']['center']['y'] == 50.0
        assert circle['geometry']['radius'] == 25.0
        assert circle['style']['fill'] == '#FFC300'
        assert circle['style']['opacity'] == 0.7
        
        # Verify text
        text = next(e for e in elements if e['type'] == 'text')
        assert text['content'] == 'PaniniFS'
        assert text['geometry']['position']['x'] == 50.0
        assert text['geometry']['position']['y'] == 55.0
        assert text['typography']['text_anchor'] == 'middle'
        assert text['typography']['font_size'] == '16'
    
    def test_svg_statistics(self):
        """Test SVG statistics computation"""
        extractor = SVGSemanticExtractor()
        result = extractor.extract('test_sample.svg')
        
        stats = result['statistics']
        assert stats['total_elements'] == 3
        assert stats['element_types']['rectangle'] == 1
        assert stats['element_types']['circle'] == 1
        assert stats['element_types']['text'] == 1
    
    def test_svg_viewbox(self):
        """Test SVG viewBox parsing"""
        extractor = SVGSemanticExtractor()
        result = extractor.extract('test_sample.svg')
        
        viewbox = result['viewBox']
        assert viewbox is not None
        assert viewbox['x'] == 0.0
        assert viewbox['y'] == 0.0
        assert viewbox['width'] == 100.0
        assert viewbox['height'] == 100.0


class TestJSONSemanticExtractor:
    """Test JSON semantic extraction"""
    
    def test_json_structure(self):
        """Test JSON structure extraction"""
        extractor = JSONSemanticExtractor()
        result = extractor.extract('test_sample.json')
        
        assert result['format'] == 'JSON'
        assert result['semantic_extraction'] is True
        assert result['root_type'] == 'object'
        
        # Verify data structure
        data = result['data']
        assert data['format'] == 'JSON'
        assert data['version'] == '1.0'
        assert 'metadata' in data
        assert 'data' in data
    
    def test_json_schema_inference(self):
        """Test JSON schema inference"""
        extractor = JSONSemanticExtractor()
        result = extractor.extract('test_sample.json')
        
        schema = result['schema']
        assert schema['type'] == 'object'
        assert 'properties' in schema
        
        # Check nested schema
        metadata_schema = schema['properties']['metadata']
        assert metadata_schema['type'] == 'object'
        
        # Check date pattern detection
        date_schema = metadata_schema['properties']['date']
        assert date_schema['pattern'] == 'date'
        
        # Check array schema
        tags_schema = metadata_schema['properties']['tags']
        assert tags_schema['type'] == 'array'
        assert tags_schema['homogeneous'] is True
    
    def test_json_statistics(self):
        """Test JSON statistics computation"""
        extractor = JSONSemanticExtractor()
        result = extractor.extract('test_sample.json')
        
        stats = result['statistics']
        assert stats['depth'] == 4
        assert stats['node_count'] == 23
        
        type_dist = stats['type_distribution']
        assert 'object' in type_dist
        assert 'string' in type_dist
        assert 'array' in type_dist
        assert 'integer' in type_dist
        assert 'number' in type_dist


class TestXMLSemanticExtractor:
    """Test XML semantic extraction"""
    
    def test_xml_basic_structure(self):
        """Test basic XML structure extraction"""
        extractor = XMLSemanticExtractor()
        result = extractor.extract('/usr/share/doc/packages/perl-XML-LibXML/example/test.xml')
        
        assert result['format'] == 'XML'
        assert result['semantic_extraction'] is True
        
        # Check root element
        root = result['root']
        assert root['type'] == 'element'
        assert root['tag'] == 'x'
        assert len(root['children']) > 0
    
    def test_xml_statistics(self):
        """Test XML statistics"""
        extractor = XMLSemanticExtractor()
        result = extractor.extract('/usr/share/doc/packages/perl-XML-LibXML/example/test.xml')
        
        stats = result['statistics']
        assert stats['total_elements'] >= 3
        assert stats['depth'] >= 2


class TestHTMLSemanticExtractor:
    """Test HTML semantic extraction"""
    
    def test_html_document_structure(self):
        """Test HTML document structure extraction"""
        extractor = HTMLSemanticExtractor()
        result = extractor.extract('test_sample.html')
        
        assert result['format'] == 'HTML'
        assert result['semantic_extraction'] is True
        assert result['version'] == 'HTML5'
        assert result['doctype'] == 'DOCTYPE html'
        
        # Check sections
        assert 'head' in result
        assert 'body' in result
        assert len(result['head']) > 0
        assert len(result['body']) > 0
    
    def test_html_semantic_elements(self):
        """Test HTML semantic element detection"""
        extractor = HTMLSemanticExtractor()
        result = extractor.extract('test_sample.html')
        
        body_elements = result['body']
        
        # Find heading
        heading = next((e for e in body_elements if e.get('semantic_type') == 'heading'), None)
        assert heading is not None
        assert heading['level'] == 1
        
        # Find list elements
        list_items = [e for e in body_elements if e.get('semantic_type') == 'list']
        assert len(list_items) == 6  # ul + 5 li elements
    
    def test_html_statistics(self):
        """Test HTML statistics"""
        extractor = HTMLSemanticExtractor()
        result = extractor.extract('test_sample.html')
        
        stats = result['statistics']
        assert stats['total_elements'] == 18
        assert stats['links'] == 1
        assert stats['images'] == 0
        assert stats['scripts'] == 1
        assert stats['styles'] == 1
        
        # Check tag distribution
        tag_dist = stats['tag_distribution']
        assert tag_dist['html'] == 1
        assert tag_dist['body'] == 1
        assert tag_dist['h1'] == 1
        assert tag_dist['li'] == 5


class TestExtractorFactory:
    """Test extractor factory function"""
    
    def test_create_svg_extractor(self):
        """Test SVG extractor creation"""
        extractor = create_extractor('svg')
        assert isinstance(extractor, SVGSemanticExtractor)
    
    def test_create_json_extractor(self):
        """Test JSON extractor creation"""
        extractor = create_extractor('json')
        assert isinstance(extractor, JSONSemanticExtractor)
    
    def test_create_xml_extractor(self):
        """Test XML extractor creation"""
        extractor = create_extractor('xml')
        assert isinstance(extractor, XMLSemanticExtractor)
    
    def test_create_html_extractor(self):
        """Test HTML extractor creation"""
        extractor = create_extractor('html')
        assert isinstance(extractor, HTMLSemanticExtractor)
        
        extractor = create_extractor('htm')
        assert isinstance(extractor, HTMLSemanticExtractor)
    
    def test_unsupported_format(self):
        """Test error handling for unsupported formats"""
        with pytest.raises(ValueError, match="No semantic extractor"):
            create_extractor('unsupported')


class TestSemanticExtractionIntegration:
    """Integration tests for semantic extraction"""
    
    def test_all_formats_extractable(self):
        """Test that all sample formats can be extracted"""
        formats = [
            ('svg', 'test_sample.svg'),
            ('json', 'test_sample.json'),
            ('html', 'test_sample.html'),
            ('xml', '/usr/share/doc/packages/perl-XML-LibXML/example/test.xml')
        ]
        
        for format_type, file_path in formats:
            extractor = create_extractor(format_type)
            result = extractor.extract(file_path)
            
            # All results should have these common fields
            assert 'format' in result
            assert 'semantic_extraction' in result
            assert result['semantic_extraction'] is True
    
    def test_semantic_vs_structural(self):
        """Test that semantic extraction goes beyond structural parsing"""
        # SVG: Extract geometric shapes, not just XML tags
        svg_extractor = SVGSemanticExtractor()
        svg_result = svg_extractor.extract('test_sample.svg')
        
        # Should have semantic geometry, not just tag names
        rect = next(e for e in svg_result['elements'] if e['type'] == 'rectangle')
        assert 'geometry' in rect
        assert 'style' in rect
        assert 'position' in rect['geometry']
        
        # JSON: Extract schema and types, not just raw data
        json_extractor = JSONSemanticExtractor()
        json_result = json_extractor.extract('test_sample.json')
        
        # Should have inferred schema
        assert 'schema' in json_result
        assert json_result['schema']['type'] == 'object'
        
        # HTML: Extract semantic elements, not just tags
        html_extractor = HTMLSemanticExtractor()
        html_result = html_extractor.extract('test_sample.html')
        
        # Should have semantic types
        body_elements = html_result['body']
        semantic_elements = [e for e in body_elements if 'semantic_type' in e]
        assert len(semantic_elements) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
