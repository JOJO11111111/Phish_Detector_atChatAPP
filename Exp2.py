import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_score, recall_score, f1_score
from datetime import datetime
import os

log_file_path = './results/Exp2_Phishintention.txt'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

def log_print(*args, **kwargs):
    from io import StringIO
    temp_out = StringIO()
    print(*args, file=temp_out, **kwargs)
    output = temp_out.getvalue()
    print(output.strip())
    with open(log_file_path, 'a') as f:
        f.write(output)

def evaluate_from_csv(csv_path):
    df = pd.read_csv(csv_path)

    label_map = {'benign': 0, 'phishing': 1}
    y_true = df['Decision'].map(label_map).values
    y_pred = df['Decision'].map(label_map).values

    log_print(f"\n=== Evaluation started at {datetime.now()} ===")
    log_print(f"CSV file: {csv_path}")
    log_print(f"Total samples: {len(df)}\n")


    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()


    precision = precision_score(y_true, y_pred, pos_label=1)
    recall = recall_score(y_true, y_pred, pos_label=1)
    f1 = f1_score(y_true, y_pred, pos_label=1)
    accuracy = accuracy_score(y_true, y_pred)


    log_print("====== FINAL EVALUATION REPORT ======")
    log_print(f"True Positives (TP): {tp}")
    log_print(f"True Negatives (TN): {tn}")
    log_print(f"False Positives (FP): {fp}")
    log_print(f"False Negatives (FN): {fn}")
    log_print(f"Precision (Phish): {precision:.4f}")
    log_print(f"Recall    (Phish): {recall:.4f}")
    log_print(f"F1 Score  (Phish): {f1:.4f}")
    log_print(f"Accuracy          : {accuracy:.4f}")
    log_print(f"\n=== Evaluation finished at {datetime.now()} ===\n")

if __name__ == "__main__":
    csv_file = "/Users/tang/PhishIntention_CyberTest/results/multimodal_results/multimodal_results.csv"
    evaluate_from_csv(csv_file)