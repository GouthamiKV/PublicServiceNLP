import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================
# 1. LOAD DATASET
# ==========================================

data = pd.read_csv("ml/dataset.csv")

print("Original dataset size:", len(data))


# ==========================================
# 2. SELECT REQUIRED COLUMNS
# ==========================================

data = data[["Complaint_Text", "Category"]]


# ==========================================
# 3. REMOVE MISSING VALUES
# ==========================================

data = data.dropna(
    subset=["Complaint_Text", "Category"]
)


# ==========================================
# 4. REMOVE DUPLICATE COMPLAINTS
# ==========================================

before = len(data)

data = data.drop_duplicates(
    subset=["Complaint_Text"]
)

after = len(data)

print("Duplicate complaints removed:", before - after)
print("Dataset size after cleaning:", after)


# ==========================================
# 5. DISPLAY CATEGORY DISTRIBUTION
# ==========================================

print("\nCategory Distribution:")
print(data["Category"].value_counts())


# ==========================================
# 6. INPUT AND OUTPUT
# ==========================================

X = data["Complaint_Text"]
y = data["Category"]


# ==========================================
# 7. TRAIN-TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==========================================
# 8. CREATE NLP + ML PIPELINE
# ==========================================

model = Pipeline([
    
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000
        )
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced"
        )
    )
])


# ==========================================
# 9. TRAIN MODEL
# ==========================================

print("\nTraining NLP model...")

model.fit(
    X_train,
    y_train
)

print("Training completed!")


# ==========================================
# 10. MAKE PREDICTIONS
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# 11. CALCULATE ACCURACY
# ==========================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n================================")
print("MODEL ACCURACY")
print("================================")

print(
    f"Accuracy: {accuracy * 100:.2f}%"
)


# ==========================================
# 12. CLASSIFICATION REPORT
# ==========================================

print("\n================================")
print("CLASSIFICATION REPORT")
print("================================")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ==========================================
# 13. CONFUSION MATRIX
# ==========================================

labels = sorted(y.unique())

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)

plt.figure(
    figsize=(12, 8)
)

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    xticklabels=labels,
    yticklabels=labels
)

plt.xlabel("Predicted Category")
plt.ylabel("Actual Category")
plt.title("Complaint Classification Confusion Matrix")

plt.xticks(rotation=45)
plt.yticks(rotation=0)

plt.tight_layout()

plt.savefig(
    "ml/confusion_matrix.png"
)

plt.show()


# ==========================================
# 14. SAVE TRAINED MODEL
# ==========================================

joblib.dump(
    model,
    "ml/complaint_model.pkl"
)

print("\n================================")
print("MODEL SAVED")
print("================================")

print(
    "Saved as: ml/complaint_model.pkl"
)