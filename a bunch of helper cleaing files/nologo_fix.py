#!/usr/bin/env python3
import csv
import os

def fix_text_decision(input_csv_path, output_csv_path, threshold=0.5):
    """
    Fixes the Text_Decision column in a CSV file based on Text Phish Score.
    
    Args:
        input_csv_path (str): Path to the input CSV file
        output_csv_path (str): Path to save the fixed CSV file
        threshold (float): Score threshold for phishing classification (default: 0.5)
    """
    print(f"Reading input CSV from: {input_csv_path}")
    
    # Check if input file exists
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file '{input_csv_path}' not found!")
        return False
    
    fixed_rows = []
    changes_count = 0
    
    # Read input CSV
    try:
        with open(input_csv_path, 'r', newline='') as csv_in:
            reader = csv.reader(csv_in)
            header = next(reader)  # Get header row
            fixed_rows.append(header)
            
            # Find column indices
            try:
                text_phish_score_idx = header.index('Text Phish Score')
                text_decision_idx = header.index('Text_Decision')
            except ValueError:
                print("Error: Required columns 'Text Phish Score' or 'Text_Decision' not found in CSV!")
                return False
            
            # Process each row
            for row in reader:
                if len(row) > max(text_phish_score_idx, text_decision_idx):
                    # Convert phish score to float
                    try:
                        phish_score = float(row[text_phish_score_idx])
                        old_decision = int(row[text_decision_idx])
                        
                        # Update decision based on threshold
                        new_decision = 1 if phish_score >= threshold else 0
                        
                        # Check if a change is needed
                        if new_decision != old_decision:
                            changes_count += 1
                            row[text_decision_idx] = str(new_decision)
                            print(f"Updated row for {row[0]}: Text Phish Score = {phish_score}, "
                                  f"Old Decision = {old_decision}, New Decision = {new_decision}")
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not process row {row[0] if row else 'unknown'}: {e}")
                
                fixed_rows.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return False
    
    # Write output CSV
    try:
        with open(output_csv_path, 'w', newline='') as csv_out:
            writer = csv.writer(csv_out)
            writer.writerows(fixed_rows)
        
        print(f"\nFixed {changes_count} rows!")
        print(f"Output saved to: {output_csv_path}")
        return True
    except Exception as e:
        print(f"Error writing CSV: {e}")
        return False

if __name__ == "__main__":
    # Hardcoded input and output paths (same for overwriting)
    input_csv_path = "/home/tiffanybao/PhishIntention/results/4.11/Multimodal/No_Logo_Phishing_predict.csv"
    output_csv_path = input_csv_path  # Overwrite the original file
    threshold = 0.5
    
    print(f"Using hardcoded path: {input_csv_path}")
    print(f"Will overwrite the original file with fixed values")
    
    # First, create a temporary file
    import tempfile
    temp_output = tempfile.mktemp(suffix='.csv')
    
    success = fix_text_decision(input_csv_path, temp_output, threshold)
    
    if success:
        # If successful, replace the original file with the fixed version
        import shutil
        shutil.move(temp_output, output_csv_path)
        print(f"Original file successfully overwritten with fixed version!")
    else:
        # If failed, clean up temp file and exit
        if os.path.exists(temp_output):
            os.remove(temp_output)
        print("Script execution failed! Original file unchanged.")