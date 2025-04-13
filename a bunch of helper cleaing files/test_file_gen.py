import os
import csv
import pandas as pd

def consolidate_datasets(info_dir, output_file):
    """
    Consolidate multiple dataset CSV files into a single test.csv file with category flags.
    
    Args:
        info_dir: Directory containing the dataset CSV files
        output_file: Path to the output consolidated CSV file
    """
    # Define the dataset categories
    categories = [
        "No_Logo_Phishing",
        "Fresh_Logo_Phishing",
        "Learned_Logo_Phishing",
        "benign_without_logo",
        "benign_with_logo"
    ]
    
    # List to store all consolidated data
    all_data = []
    
    print(f"Starting to consolidate datasets from {info_dir}...")
    
    # Process each dataset file
    for category in categories:
        csv_file = os.path.join(info_dir, f"{category}.csv")
        
        if not os.path.exists(csv_file):
            print(f"Warning: File {csv_file} does not exist, skipping...")
            continue
            
        print(f"Processing {category} dataset...")
        
        try:
            # Read the CSV file
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Process each row
                for row in reader:
                    # Create a new row with the consolidated format
                    new_row = {
                        'folder_name': row.get('New Folder Name', ''),
                        'url': row.get('URL', ''),
                        'is_No_Logo_Phishing': 1 if category == 'No_Logo_Phishing' else 0,
                        'is_Fresh_Logo_Phishing': 1 if category == 'Fresh_Logo_Phishing' else 0,
                        'is_Learned_Logo_Phishing': 1 if category == 'Learned_Logo_Phishing' else 0,
                        'is_benign_without_logo': 1 if category == 'benign_without_logo' else 0,
                        'is_benign_with_logo': 1 if category == 'benign_with_logo' else 0,
                        'label': row.get('label', '')
                    }
                    
                    all_data.append(new_row)
                    
            print(f"Added {len(all_data)} entries from {category}")
                
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Write the consolidated data to a CSV file
    if all_data:
        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(all_data)
            
            # Make sure the 'label' column has the correct values (1 for phishing, 0 for benign)
            df['label'] = df.apply(
                lambda x: 1 if (x['is_No_Logo_Phishing'] == 1 or 
                                x['is_Fresh_Logo_Phishing'] == 1 or 
                                x['is_Learned_Logo_Phishing'] == 1) else 0, 
                axis=1
            )
            
            # Write to CSV
            df.to_csv(output_file, index=False)
            print(f"Successfully written {len(df)} entries to {output_file}")
            
            # Print dataset statistics
            print("\nDataset Statistics:")
            print(f"Total samples: {len(df)}")
            for category in categories:
                column_name = f"is_{category}"
                if column_name in df.columns:
                    count = df[column_name].sum()
                    print(f"{category}: {count} samples")
                    
            phishing_count = df['label'].sum()
            benign_count = len(df) - phishing_count
            print(f"Total phishing samples: {phishing_count}")
            print(f"Total benign samples: {benign_count}")
            
        except Exception as e:
            print(f"Error creating consolidated file: {e}")
    else:
        print("No data collected, output file not created.")

if __name__ == "__main__":
    # Define paths
    info_dir = "/home/tiffanybao/PhishIntention/datasets/info_about_datasets"
    output_file = "/home/tiffanybao/PhishIntention/datasets/test.csv"
    
    # Run consolidation
    consolidate_datasets(info_dir, output_file)