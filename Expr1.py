import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, confusion_matrix, roc_auc_score
)
def load_model_results(txt_path):
    """Load model predictions from txt file with None handling"""
    results = []
    with open(txt_path, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 6:  # Ensure valid line format
                try:
                    confidence = float(parts[5]) if parts[5] != 'None' else 0.0
                except ValueError:
                    confidence = 0.0  # Fallback for any invalid number
                
                results.append({
                    'website': parts[0],
                    'url': parts[1],
                    'prediction': int(parts[2]),
                    'pred_target': parts[3],
                    'matched_domain': eval(parts[4]) if parts[4] != 'None' else None,
                    'confidence': confidence,  # Use the safely parsed value
                    'runtime': parts[6].split('|') if len(parts) > 6 else None
                })
    return pd.DataFrame(results)

def evaluate_model(pred_df, truth_csv):
    """Calculate performance metrics"""
    # Load ground truth - use 'Original Folder Name' as the website identifier
    truth_df = pd.read_csv(truth_csv)
    truth_df = truth_df.rename(columns={'Original Folder Name': 'website'})
    
    # Merge predictions with ground truth on website names
    merged = pred_df.merge(truth_df, on='website', how='inner')
    
    if merged.empty:
        raise ValueError("No matching websites between predictions and ground truth")
    
    y_true = merged['label']
    y_pred = merged['prediction']
    y_conf = merged['confidence']
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'f1': f1_score(y_true, y_pred),
        # 'roc_auc': roc_auc_score(y_true, y_conf),  # Using confidence scores
        'confusion_matrix': confusion_matrix(y_true, y_pred),
        'total_samples': len(merged),
        'phishing_samples': sum(y_true),
        'benign_samples': len(y_true) - sum(y_true)
    }
    
    # Additional detailed analysis
    metrics['false_positives'] = merged[(merged['prediction'] == 1) & (merged['label'] == 0)]
    metrics['false_negatives'] = merged[(merged['prediction'] == 0) & (merged['label'] == 1)]
    
    return metrics

def print_metrics(metrics):
    """Pretty print evaluation results"""
    print(f"\n{' Evaluation Results ':=^60}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1']:.4f}")
    # print(f"ROC AUC: {metrics['roc_auc']:.4f}")
    print(f"\nConfusion Matrix:\n{metrics['confusion_matrix']}")
    print(f"\nSamples: {metrics['total_samples']} (Phishing: {metrics['phishing_samples']}, Benign: {metrics['benign_samples']})")
    
    if not metrics['false_positives'].empty:
        print("\nFalse Positives (Benign detected as Phishing):")
        print(metrics['false_positives'][['website', 'url', 'confidence']])
    
    if not metrics['false_negatives'].empty:
        print("\nFalse Negatives (Phishing missed):")
        print(metrics['false_negatives'][['website', 'url', 'confidence']])

if __name__ == "__main__":
    # Load data
    predictions = load_model_results("/home/tiffanybao/PhishIntention/results/4.9/Original/Learned_logo_phishing.txt")  # Your model's output
    ground_truth = "/home/tiffanybao/PhishIntention/datasets/Learned_Logo_Phishing.csv"  # Your test CSV
    
    # Evaluate
    metrics = evaluate_model(predictions, ground_truth)
    print_metrics(metrics)
    
    # Save detailed results
    pd.DataFrame.from_dict(metrics, orient='index').to_csv("evaluation_report.csv")