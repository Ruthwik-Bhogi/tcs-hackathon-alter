# models/train_xgb.py
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from pathlib import Path
import argparse

def featurize(df):
    # df: time series with columns like ED_count, ICU_count, Ward_count
    df = df.copy()
    df = df.sort_values("time")
    for d in ["ED","ICU","Ward"]:
        df[f"{d}_lag1"] = df[f"{d}_count"].shift(1).fillna(method="bfill")
        df[f"{d}_diff1"] = df[f"{d}_count"] - df[f"{d}_lag1"]
    df["hour"] = df["time"].dt.hour
    df["weekday"] = df["time"].dt.weekday
    return df.dropna()

def train(df, target="ED_count", horizon=4, out_path="models/xgb_model.pkl"):
    df = featurize(df)
    # create horizon target: occupancy after horizon hours
    df[f"target_{horizon}h"] = df[target].shift(-horizon)
    df = df.dropna()
    X = df[[c for c in df.columns if c not in ["time", target, f"target_{horizon}h"] and not c.endswith("_count")]]
    y = df[f"target_{horizon}h"]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.1, tree_method="hist")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=20, verbose=False)
    joblib.dump(model, out_path)
    print("Saved model to", out_path)
    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="sim_data.csv")
    parser.add_argument("--out", default="models/xgb_model.pkl")
    parser.add_argument("--target", default="ED_count")
    parser.add_argument("--horizon", type=int, default=4)
    args = parser.parse_args()
    df = pd.read_csv(args.data, parse_dates=["time"])
    train(df, target=args.target, horizon=args.horizon, out_path=args.out)
