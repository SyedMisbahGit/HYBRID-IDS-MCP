"""
Smart Data Sampler for CIC-IDS2017

Solves the "Big Data" problem by reading large CSVs in chunks and creating
a balanced, manageable dataset for training.

Strategy:
- Read raw CSVs in chunks (to avoid OOM)
- Keep 100% of Attack samples (Web Attacks, Bot, Infiltration, etc.)
- Keep 10% of Benign samples (Randomly sampled)
- Save to data/processed/train_nids_sampled.csv
"""

import pandas as pd
import numpy as np
import os
import glob
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def smart_sample(
    input_dir='data/raw/cicids2017',
    output_file='data/processed/train_nids_sampled.csv',
    benign_ratio=0.1,
    chunk_size=100000
):
    """
    Perform smart stratified sampling on CIC-IDS2017 dataset
    """
    logger.info("="*60)
    logger.info("Starting Smart Data Sampling")
    logger.info("="*60)
    logger.info(f"Input Directory: {input_dir}")
    logger.info(f"Output File: {output_file}")
    logger.info(f"Benign Ratio: {benign_ratio*100}%")
    
    # Check input directory
    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        logger.info("Please run: python scripts/download_manager.py")
        return False
        
    # Get list of CSV files
    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    if not csv_files:
        logger.error("No CSV files found in input directory")
        return False
        
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize counters
    total_rows = 0
    sampled_rows = 0
    stats = {'BENIGN': 0}
    
    # Process each file
    processed_chunks = []
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        logger.info(f"Processing: {filename}")
        
        try:
            # Read in chunks
            with pd.read_csv(file_path, chunksize=chunk_size, encoding='cp1252', low_memory=False) as reader:
                for chunk in reader:
                    # Clean column names (strip whitespace)
                    chunk.columns = chunk.columns.str.strip()
                    
                    # Handle Label column (sometimes it has spaces)
                    if 'Label' not in chunk.columns:
                        logger.warning(f"Label column not found in {filename}")
                        continue
                        
                    # Filter data
                    # 1. Attacks: Keep ALL
                    attacks = chunk[chunk['Label'] != 'BENIGN']
                    
                    # 2. Benign: Sample 10%
                    benign = chunk[chunk['Label'] == 'BENIGN']
                    if not benign.empty:
                        benign_sampled = benign.sample(frac=benign_ratio, random_state=42)
                    else:
                        benign_sampled = pd.DataFrame()
                    
                    # Combine
                    sampled_chunk = pd.concat([attacks, benign_sampled])
                    
                    # Update stats
                    total_rows += len(chunk)
                    sampled_rows += len(sampled_chunk)
                    
                    # Count labels in this chunk
                    chunk_stats = sampled_chunk['Label'].value_counts().to_dict()
                    for label, count in chunk_stats.items():
                        stats[label] = stats.get(label, 0) + count
                    
                    processed_chunks.append(sampled_chunk)
                    
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            
    if not processed_chunks:
        logger.error("No data processed!")
        return False
        
    # Concatenate all chunks
    logger.info("Concatenating chunks...")
    final_df = pd.concat(processed_chunks, ignore_index=True)
    
    # Shuffle dataset
    logger.info("Shuffling dataset...")
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to CSV
    logger.info(f"Saving to {output_file}...")
    final_df.to_csv(output_file, index=False)
    
    logger.info("="*60)
    logger.info("[SUCCESS] Sampling Complete!")
    logger.info(f"Original Rows (Approx): {total_rows:,}")
    logger.info(f"Sampled Rows: {sampled_rows:,}")
    logger.info(f"Reduction: {(1 - sampled_rows/total_rows)*100:.1f}%")
    logger.info("-" * 30)
    logger.info("Class Distribution:")
    for label, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {label}: {count:,}")
    logger.info("="*60)
    
    return True

if __name__ == "__main__":
    smart_sample()
