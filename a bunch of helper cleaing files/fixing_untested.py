#!/usr/bin/env python3

import os
import shutil
import pandas as pd

def main():
    # Define file and folder paths
    csv_path = "/home/tiffanybao/PhishIntention/results/4.11/Multimodal/Fresh_Logo_Phishing_predict.csv"
    dataset_path = "/home/tiffanybao/PhishIntention/datasets/Fresh_Logo_Phishing"
    untested_folder_name = "untested fresh logo phishing"
    
    # Create full path for untested folder destination (create it in the same directory as the dataset)
    untested_path = os.path.join(os.path.dirname(dataset_path), untested_folder_name)
    
    # Ensure the untested folder exists; if not, create it
    if not os.path.exists(untested_path):
        os.makedirs(untested_path)
        print(f"Created directory for untested folders: {untested_path}")
    
    # Read the CSV file into a DataFrame; assume the first column contains the folder names.
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Check if the expected column exists; you may need to adjust if headers differ.
    expected_column = "Site Folder"
    if expected_column not in df.columns:
        print(f"Expected column '{expected_column}' not found in CSV. Columns present: {df.columns.tolist()}")
        return
    
    # Get a list of tested folder names from the CSV file (assume each entry is unique)
    tested_folders = set(df[expected_column].astype(str).str.strip())
    print(f"Number of tested folders from CSV: {len(tested_folders)}")
    
    # List all items in the dataset_path and filter for folders
    all_items = os.listdir(dataset_path)
    all_folders = [item for item in all_items if os.path.isdir(os.path.join(dataset_path, item))]
    print(f"Total folders in dataset directory: {len(all_folders)}")
    
    # Determine untested folders by set difference
    untested_folders = [folder for folder in all_folders if folder not in tested_folders]
    print(f"Number of untested folders identified: {len(untested_folders)}")
    
    # If untested folders exist, move them to the new untested folder location
    if untested_folders:
        for folder in untested_folders:
            src = os.path.join(dataset_path, folder)
            dest = os.path.join(untested_path, folder)
            try:
                shutil.move(src, dest)
                print(f"Moved folder '{folder}' to '{untested_path}'")
            except Exception as e:
                print(f"Error moving folder '{folder}': {e}")
    else:
        print("No untested folders to move.")

if __name__ == "__main__":
    main()
