# currently just test on a small amount of dataset
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

def load_results(file_path):
    """Load results file into DataFrame"""
    df = pd.read_csv(file_path, sep='\t', header=None, 
                    names=['folder', 'url', 'phish_category', 'pred_target', 
                          'matched_domain', 'siamese_conf', 'used_gpt'],
                    encoding='ISO-8859-1')
    return df

def evaluate_models(original_df, modified_df):
    """Compare performance metrics between models"""
    
    # Merge results on URL
    merged = pd.merge(original_df, modified_df, on='url', 
                     suffixes=('_orig', '_mod'))
    
    # Get ground truth labels (you'll need to provide this)
    # For demonstration, assuming you have a way to get true labels
    merged['true_label'] = ...  # Add your ground truth
    
    # Calculate metrics for original model
    orig_metrics = {
        'accuracy': accuracy_score(merged['true_label'], merged['phish_category_orig']),
        'precision': precision_score(merged['true_label'], merged['phish_category_orig']),
        'recall': recall_score(merged['true_label'], merged['phish_category_orig']),
        'f1': f1_score(merged['true_label'], merged['phish_category_orig'])
    }
    
    # Calculate metrics for modified model
    mod_metrics = {
        'accuracy': accuracy_score(merged['true_label'], merged['phish_category_mod']),
        'precision': precision_score(merged['true_label'], merged['phish_category_mod']),
        'recall': recall_score(merged['true_label'], merged['phish_category_mod']),
        'f1': f1_score(merged['true_label'], merged['phish_category_mod'])
    }
    
    # Cases where GPT helped
    gpt_cases = merged[(merged['used_gpt'] == 1) & 
                      (merged['phish_category_mod'] != merged['phish_category_orig'])]
    
    return {
        'original_metrics': orig_metrics,
        'modified_metrics': mod_metrics,
        'gpt_improvement_cases': len(gpt_cases),
        'gpt_success_rate': len(gpt_cases[gpt_cases['phish_category_mod'] == merged['true_label']]) / len(gpt_cases)
    }

if __name__ == "__main__":
    # Load results
    original_results = load_results("Phishintention_results.txt")
    modified_results = load_results("ImageLLM+Phishintention_results.txt")
    
    # Evaluate
    metrics = evaluate_models(original_results, modified_results)
    
    # Print results
    print("=== Original Model ===")
    print(f"Accuracy: {metrics['original_metrics']['accuracy']:.2f}")
    print(f"Recall: {metrics['original_metrics']['recall']:.2f}")
    print(f"Precision: {metrics['original_metrics']['precision']:.2f}")
    print(f"F1: {metrics['original_metrics']['f1']:.2f}")
    
    print("\n=== Modified Model ===")
    print(f"Accuracy: {metrics['modified_metrics']['accuracy']:.2f}")
    print(f"Recall: {metrics['modified_metrics']['recall']:.2f}")
    print(f"Precision: {metrics['modified_metrics']['precision']:.2f}")
    print(f"F1: {metrics['modified_metrics']['f1']:.2f}")
    
    print(f"\nGPT helped in {metrics['gpt_improvement_cases']} cases")
    print(f"GPT success rate: {metrics['gpt_success_rate']:.2f}")