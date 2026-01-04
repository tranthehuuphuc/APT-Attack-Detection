#!/usr/bin/env python3
"""
Process PDF CTI reports with g4f to extract MITRE techniques and IOCs

This demonstrates the LLM-based CTI processing workflow using static PDF files.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
    except ImportError:
        logger.error("PyPDF2 not installed. Run: pip install PyPDF2")
        sys.exit(1)
    
    logger.info(f"Extracting text from: {pdf_path}")
    
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text_parts = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            text_parts.append(text)
            logger.debug(f"  Page {i+1}: {len(text)} chars")
        
        full_text = "\n\n".join(text_parts)
        logger.info(f"  Total extracted: {len(full_text)} characters from {len(reader.pages)} pages")
        
        return full_text

def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """Split text into chunks for LLM processing."""
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        if current_size + para_size > max_chunk_size and current_chunk:
            # Save current chunk
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Don't forget last chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    logger.info(f"Split into {len(chunks)} chunks")
    return chunks

def process_chunk_with_g4f(chunk: str, mitre_techniques: List[str]) -> Dict[str, Any]:
    """Process a text chunk with g4f to extract techniques and IOCs."""
    # Import agent modules
    from src.pipeline.agent.llm_g4f import call_g4f
    
    # Create extraction prompt
    prompt = f"""Analyze the following cybersecurity threat report and extract:
1. MITRE ATT&CK technique IDs (e.g., T1566, T1059.001)
2. Indicators of Compromise (IOCs) like file hashes, IPs, domains, URLs

Return ONLY valid JSON in this exact format:
{{
  "techniques": [
    {{"technique_id": "T1566.001", "name": "Spearphishing Attachment", "confidence": 0.85}}
  ],
  "indicators": [
    {{"type": "ip_address", "value": "192.0.2.1"}},
    {{"type": "file_hash", "value": "d41d8cd98f00b204e9800998ecf8427e"}}
  ]
}}

Common MITRE techniques to look for: {', '.join(mitre_techniques[:20])}

Report text:
{chunk[:3000]}
"""
    
    try:
        result = call_g4f(prompt, schema={"name": "EXTRACT_SCHEMA"})
        return result
    except Exception as e:
        logger.warning(f"g4f processing failed: {e}")
        return {"techniques": [], "indicators": []}

def merge_results(chunks_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge results from multiple chunks."""
    all_techniques = []
    all_indicators = []
    
    # Track seen items to avoid duplicates
    seen_tech_ids = set()
    seen_indicators = set()
    
    for result in chunks_results:
        # Merge techniques
        for tech in result.get('techniques', []):
            tech_id = tech.get('technique_id')
            if tech_id and tech_id not in seen_tech_ids:
                all_techniques.append(tech)
                seen_tech_ids.add(tech_id)
        
        # Merge indicators
        for ind in result.get('indicators', []):
            ind_key = f"{ind.get('type')}:{ind.get('value')}"
            if ind_key not in seen_indicators:
                all_indicators.append(ind)
                seen_indicators.add(ind_key)
    
    return {
        'techniques': all_techniques,
        'indicators': all_indicators,
        'metadata': {
            'chunks_processed': len(chunks_results),
            'extraction_method': 'pdf_g4f'
        }
    }

def load_mitre_techniques(mitre_file: str) -> List[str]:
    """Load MITRE technique IDs from STIX file."""
    with open(mitre_file, 'r') as f:
        data = json.load(f)
    
    techniques = []
    for obj in data.get('objects', []):
        if obj.get('type') == 'attack-pattern':
            for ref in obj.get('external_references', []):
                if ref.get('source_name') == 'mitre-attack':
                    techniques.append(ref.get('external_id'))
                    break
    
    return techniques

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Process PDF CTI reports with g4f')
    parser.add_argument('--pdf-dir', default='data/cti_reports/pdfs',
                        help='Directory containing PDF files')
    parser.add_argument('--mitre-file', default='data/mitre/enterprise-attack.json',
                        help='MITRE ATT&CK STIX file')
    parser.add_argument('--output', default='runs/cti/seeds.json',
                        help='Output seeds file')
    parser.add_argument('--max-pdfs', type=int, default=5,
                        help='Maximum PDFs to process')
    
    args = parser.parse_args()
    
    # Check PDF directory
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        logger.info("Creating directory. Please add PDF files there.")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        sys.exit(1)
    
    # Find PDF files
    pdf_files = list(pdf_dir.glob('*.pdf'))
    if not pdf_files:
        logger.error(f"No PDF files found in: {pdf_dir}")
        logger.info("Please add CTI report PDFs to that directory")
        sys.exit(1)
    
    pdf_files = pdf_files[:args.max_pdfs]
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Load MITRE techniques for prompting
    logger.info(f"Loading MITRE techniques from: {args.mitre_file}")
    mitre_techniques = load_mitre_techniques(args.mitre_file)
    logger.info(f"Loaded {len(mitre_techniques)} MITRE techniques")
    
    # Process each PDF
    all_results = []
    
    for pdf_file in pdf_files:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {pdf_file.name}")
        logger.info(f"{'='*70}")
        
        try:
            # Extract text
            text = extract_text_from_pdf(str(pdf_file))
            
            if len(text) < 100:
                logger.warning(f"  Too little text extracted ({len(text)} chars). Skipping.")
                continue
            
            # Chunk text
            chunks = chunk_text(text, max_chunk_size=3500)
            
            # Process chunks
            logger.info(f"Processing {len(chunks)} chunks with g4f...")
            chunk_results = []
            
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"  Chunk {i}/{len(chunks)}...")
                result = process_chunk_with_g4f(chunk, mitre_techniques)
                chunk_results.append(result)
                
                # Log what we got
                tech_count = len(result.get('techniques', []))
                ind_count = len(result.get('indicators', []))
                logger.info(f"    Extracted: {tech_count} techniques, {ind_count} indicators")
            
            # Merge chunk results
            pdf_result = merge_results(chunk_results)
            all_results.append(pdf_result)
            
            logger.info(f"✅ {pdf_file.name}: {len(pdf_result['techniques'])} techniques, {len(pdf_result['indicators'])} indicators")
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_file.name}: {e}", exc_info=True)
            continue
    
    # Merge all PDFs
    logger.info(f"\n{'='*70}")
    logger.info("Merging results from all PDFs...")
    logger.info(f"{'='*70}")
    
    final_result = merge_results(all_results)
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(final_result, indent=2))
    
    # Report
    print("\n" + "="*70)
    print("✅ PDF CTI Processing Complete (g4f)")
    print("="*70)
    print(f"\nProcessed: {len(pdf_files)} PDF files")
    print(f"Output: {args.output}")
    print(f"\nExtracted:")
    print(f"  Techniques: {len(final_result['techniques'])}")
    print(f"  Indicators: {len(final_result['indicators'])}")
    print(f"\nTop Techniques:")
    for i, tech in enumerate(final_result['techniques'][:10], 1):
        print(f"  {i}. {tech.get('technique_id')} - {tech.get('name')}")
    print("="*70)

if __name__ == "__main__":
    main()
