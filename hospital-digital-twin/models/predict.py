# models/predict.py
import joblib
import pandas as pd
from models.train_xgb import featurize
import numpy as np

class Predictor:
    def __init__(self, model_path="models/xgb_model.pkl"):
        self.model = joblib.load(model_path)

    def predict_horizon(self, df_recent):
        # df_recent: last N rows including time
        X = featurize(df_recent).iloc[-1:]
        # drop time and count columns
        X = X[[c for c in X.columns if not c.endswith("_count") and c!="time"]]
        pred = self.model.predict(X)[0]
        return float(pred)
