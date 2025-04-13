import os
import csv
import shutil
from datetime import datetime

def check_and_clean_folders(base_path, report_file):
    """
    Check all website folders and remove those that don't contain both html.txt and info.txt files.
    
    Args:
        base_path: Path to the dataset directory
        report_file: Path to the CSV report file
    """
    # Get all subfolders
    subfolders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    total_folders = len(subfolders)
    
    # Process each folder and collect results
    results = []
    removed_count = 0
    kept_count = 0
    
    for folder in subfolders:
        folder_path = os.path.join(base_path, folder)
        html_path = os.path.join(folder_path, 'html.txt')
        info_path = os.path.join(folder_path, 'info.txt')
        
        # Check if both files exist
        has_html = os.path.exists(html_path)
        has_info = os.path.exists(info_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"Checking folder: {folder}")
        print(f"  Has HTML: {has_html}")
        print(f"  Has Info: {has_info}")
        
        if not (has_html and has_info):
            # Remove the folder if either file is missing
            try:
                print(f"  Removing folder due to missing required files")
                shutil.rmtree(folder_path)
                action = "Removed"
                removed_count += 1
            except Exception as e:
                print(f"  Error removing folder: {e}")
                action = f"Error removing: {e}"
        else:
            print(f"  Folder has all required files, keeping it")
            action = "Kept"
            kept_count += 1
        
        # Store result
        results.append([folder, has_html, has_info, action, timestamp])
    
    # Now write to the report with summary at the top
    with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write summary at the top
        csv_writer.writerow(['SUMMARY INFORMATION'])
        csv_writer.writerow(['Dataset', base_path])
        csv_writer.writerow(['Total Folders Before Cleaning', total_folders])
        csv_writer.writerow(['Folders Removed', removed_count])
        csv_writer.writerow(['Folders Remaining', kept_count])
        csv_writer.writerow(['Report Generated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        csv_writer.writerow([])  # Empty row as separator
        
        # Write the header for detailed results
        csv_writer.writerow(['Folder Name', 'Has HTML', 'Has Info', 'Action', 'Timestamp'])
        
        # Write all the detailed results
        for result in results:
            csv_writer.writerow(result)
    
    print(f"\nChecking complete!")
    print(f"Total folders checked: {total_folders}")
    print(f"Folders kept (had all required files): {kept_count}")
    print(f"Folders removed (missing files): {removed_count}")
    print(f"Report saved to: {report_file}")
    
    return kept_count  # Return count of remaining folders for overall summary

if __name__ == "__main__":
    # Set paths - using the same base path structure
    dataset_paths = [
        "datasets/No_Logo_Phishing",
        "datasets/Fresh_Logo_Phishing",
        "datasets/Learned_Logo_Phishing",
        "datasets/benign_with_logo",
        "datasets/benign_without_logo"
        # "datasets/benign",

    ]
    
    # Create overall summary report
    overall_summary_path = "datasets_cleaning_summary.csv"
    with open(overall_summary_path, 'w', newline='', encoding='utf-8') as summary_file:
        summary_writer = csv.writer(summary_file)
        summary_writer.writerow(['Dataset', 'Total Folders Before', 'Folders Removed', 'Folders Remaining'])
    
    # Process each dataset
    for path in dataset_paths:
        if os.path.exists(path):
            print(f"\nProcessing {path}...")
            total_before = len([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))])
            
            report_path = f"{path.replace('/', '_')}_html_check_report.csv"
            remaining = check_and_clean_folders(path, report_path)
            
            # Add to overall summary
            with open(overall_summary_path, 'a', newline='', encoding='utf-8') as summary_file:
                summary_writer = csv.writer(summary_file)
                summary_writer.writerow([path, total_before, total_before - remaining, remaining])
        else:
            print(f"\nWarning: Path {path} does not exist, skipping...")
            # Record in overall summary that path doesn't exist
            with open(overall_summary_path, 'a', newline='', encoding='utf-8') as summary_file:
                summary_writer = csv.writer(summary_file)
                summary_writer.writerow([path, 'N/A', 'N/A', 'Directory not found'])
    
    print(f"\nAll datasets processed. Overall summary saved to {overall_summary_path}")