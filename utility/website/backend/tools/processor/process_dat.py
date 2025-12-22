#!/usr/bin/env python3
"""
Main script to process DAT files:
1. Detect character and color
2. Generate CSP 
3. Output organized results
"""

import os
import sys
import shutil
from pathlib import Path
from detect_character import DATParser
from generate_csp import generate_csp
from validate_costume import validate_dat_file
from generate_stock_icon import generate_stock_icon

def process_dat_file(dat_filepath):
    """
    Complete processing of a DAT file:
    - Detect character and color
    - Generate CSP
    - Return all information
    """
    
    # print(f"\n{'='*60}")
    # print(f"Processing: {os.path.basename(dat_filepath)}")
    # print('='*60)

    # Step 1: Detect character and color
    # print("Step 1: Detecting character and color...")

    parser = DATParser(dat_filepath)
    try:
        parser.read_dat()
        character, symbol = parser.detect_character()
        color = parser.detect_costume_color()

        if character:
            # print(f"✓ Character: {character}")
            # print(f"✓ Color: {color}")
            # print(f"✓ Symbol: {symbol}")
            pass
        else:
            # print("✗ Could not detect character")
            return None

    except Exception as e:
        # print(f"✗ Error parsing DAT: {e}")
        return None
    
    # Step 2: Validate for Slippi compatibility (using temp copy to avoid modifying original)
    # print(f"\nStep 2: Validating Slippi compatibility...")

    # Create temp copy with proper naming for validator (needs PlXxYy.dat format)
    temp_file = Path(dat_filepath).parent / "PlTmPx.dat"  # Use PlTmPx as temp name
    shutil.copy2(dat_filepath, temp_file)

    try:
        validation_result = validate_dat_file(temp_file, auto_fix=False, create_backup=False)

        if validation_result['is_valid'] and not validation_result['needs_fix']:
            # print(f"✓ File is Slippi-safe")
            slippi_status = 'valid'
        elif validation_result['needs_fix']:
            # print(f"⚠ File needs fixes for Slippi")
            # print(f"  Issues: {validation_result['output']}")
            slippi_status = 'needs_fix'
        else:
            # print(f"✗ Validation error: {validation_result['output']}")
            slippi_status = 'error'
    finally:
        # Clean up temp file
        if temp_file.exists():
            os.remove(temp_file)

    # Step 3: Generate CSP
    # print(f"\nStep 3: Generating CSP...")

    try:
        csp_path = generate_csp(dat_filepath)
        if csp_path:
            # print(f"✓ CSP generated: {os.path.basename(csp_path)}")
            pass
        else:
            # print("✗ CSP generation failed")
            csp_path = None
    except Exception as e:
        # print(f"✗ Error generating CSP: {e}")
        csp_path = None

    # Step 4: Generate Stock Icon
    # print(f"\nStep 4: Generating Stock Icon...")

    stock_path = None
    if csp_path:
        # Generate stock icon filename
        dat_dir = os.path.dirname(os.path.abspath(dat_filepath))
        dat_name = os.path.splitext(os.path.basename(dat_filepath))[0]
        stock_output = os.path.join(dat_dir, f"{dat_name}_stock.png")

        try:
            stock_path = generate_stock_icon(csp_path, character, stock_output)
            # if stock_path:
            #     print(f"✓ Stock icon generated: {os.path.basename(stock_path)}")
            # else:
            #     print("✗ Stock icon generation failed")
        except Exception as e:
            # print(f"✗ Error generating stock icon: {e}")
            stock_path = None

    # Step 5: Return results
    result = {
        'file': dat_filepath,
        'character': character,
        'color': color,
        'symbol': symbol,
        'slippi_safe': slippi_status == 'valid',
        'slippi_status': slippi_status,
        'csp_path': csp_path,
        'stock_path': stock_path,
        'success': csp_path is not None
    }

    # Clean API-like output
    print({
        'character': character,
        'color': color,
        'slippi_status': slippi_status,
        'csp_generated': csp_path is not None,
        'csp_path': csp_path,
        'stock_generated': stock_path is not None,
        'stock_path': stock_path
    })

    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 process_dat.py <dat_file> [dat_file2] ...")
        print("Example: python3 process_dat.py 'pichu nr.dat' 'yoshi ys.dat'")
        sys.exit(1)
    
    results = []
    
    for dat_file in sys.argv[1:]:
        if not os.path.exists(dat_file):
            print(f"File not found: {dat_file}")
            continue
            
        result = process_dat_file(dat_file)
        if result:
            results.append(result)
    
    # Summary
    # print(f"\n{'='*60}")
    # print("SUMMARY")
    # print('='*60)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    # print(f"Total files processed: {len(results)}")
    # print(f"Successful: {len(successful)}")
    # print(f"Failed: {len(failed)}")

    # if successful:
    #     print(f"\nSuccessful files:")
    #     for result in successful:
    #         filename = os.path.basename(result['file'])
    #         print(f"  {filename} → {result['character']} ({result['color']})")

    # if failed:
    #     print(f"\nFailed files:")
    #     for result in failed:
    #         filename = os.path.basename(result['file'])
    #         print(f"  {filename}")

if __name__ == "__main__":
    main()