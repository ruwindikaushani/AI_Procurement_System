import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv("vendor_dataset.csv")

# ============================================================
# FEATURES
# ============================================================

X = df[
    [
        "PriceScore",
        "QualityScore",
        "DeliveryScore",
        "ComplaintCount",
        "ReliabilityScore",
        "OnTimeDeliveryRate",
        "ContractValue",
        "VendorScore"
    ]
]

# ============================================================
# TARGET
# ============================================================

y = df["RiskLevel"]

# ============================================================
# SPLIT DATASET
# 80% Training / 20% Testing
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# ============================================================
# TRAIN RANDOM FOREST MODEL
# ============================================================

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# ============================================================
# PREDICTIONS
# ============================================================

y_pred = model.predict(X_test)

# ============================================================
# MODEL EVALUATION
# ============================================================

accuracy = accuracy_score(y_test, y_pred)

precision = precision_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n========================================")
print("       ML MODEL EVALUATION")
print("========================================")

print("Model: Random Forest Classifier")
print("Training Samples:", len(X_train))
print("Testing Samples:", len(X_test))

print("----------------------------------------")
print("Accuracy :", round(accuracy * 100, 2), "%")
print("Precision:", round(precision * 100, 2), "%")
print("Recall   :", round(recall * 100, 2), "%")
print("F1-Score :", round(f1 * 100, 2), "%")

# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n========================================")
print("       CLASSIFICATION REPORT")
print("========================================")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

# ============================================================
# CONFUSION MATRIX
# ============================================================

print("========================================")
print("       CONFUSION MATRIX")
print("========================================")

labels = sorted(y.unique())

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)

print("Risk Levels:", labels)
print(cm)

# ============================================================
# SAVE MODEL
# ============================================================

with open("model/risk_model.pkl", "wb") as file:
    pickle.dump(model, file)

print("\n========================================")
print("Model Trained Successfully!")
print("Model saved successfully!")
print("========================================")