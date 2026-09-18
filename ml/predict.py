import joblib


# Load trained model
model = joblib.load(
    "ml/complaint_model.pkl"
)


def predict_complaint(text):

    prediction = model.predict([text])

    probabilities = model.predict_proba([text])

    category = prediction[0]

    confidence = max(
        probabilities[0]
    )

    return category, confidence


# ==========================================
# TEST THE MODEL
# ==========================================

if __name__ == "__main__":

    complaint = input(
        "\nEnter your complaint: "
    )

    category, confidence = predict_complaint(
        complaint
    )
    department = DEPARTMENT_MAP.get(
    category,
    "General Municipal Department"
)

    print("\n------------------------------")
    print("PREDICTION")
    print("------------------------------")

    print(
        "Predicted Domain:",
        category
    )

    print(
        f"Confidence: {confidence * 100:.2f}%"
    )