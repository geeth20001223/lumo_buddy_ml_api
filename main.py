from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="LUMO BUDDY ML API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path("model/autism_model.pkl")

model_package = joblib.load(MODEL_PATH)
model = model_package["model"]
feature_names = model_package["feature_names"]


class SurveyInput(BaseModel):
    emotion_score: int
    cognitive_score: int
    self_awareness_score: int
    math_score: int
    total_score: int


def convert_survey_to_model_input(data: SurveyInput):
    base_values = [
        data.emotion_score,
        data.cognitive_score,
        data.self_awareness_score,
        data.math_score,
        data.total_score,
    ]

    values = []
    for i in range(len(feature_names)):
        values.append(base_values[i % len(base_values)])

    return pd.DataFrame([values], columns=feature_names)


def convert_total_score_to_level(total_score: int):
    if total_score <= 40:
        return 1
    elif total_score <= 85:
        return 2
    return 3


@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "LUMO BUDDY ML API is working",
    }


@app.post("/predict")
def predict(data: SurveyInput):
    input_df = convert_survey_to_model_input(data)

    prediction = model.predict(input_df)[0]

    confidence = 0.0
    if hasattr(model, "predict_proba"):
        confidence = float(max(model.predict_proba(input_df)[0]))

    predicted_level = convert_total_score_to_level(data.total_score)

    return {
        "screening_prediction": int(prediction),
        "predicted_level": predicted_level,
        "confidence": round(confidence, 2),
        "recommendation": f"Suggested game level: Level {predicted_level}",
    }