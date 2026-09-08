"""
ML / AI models for Soft Rent a Car.
All models are trained on the fly and cached via st.cache_data.
"""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings("ignore")


# ── 1. Driver Safety Scorer ───────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def train_driver_safety_model(telem_df: pd.DataFrame, drivers_df: pd.DataFrame):
    """
    Predict driver behavior_profile label from telematics features.
    Target: excellent / good / average / poor / dangerous
    """
    df = telem_df.merge(
        drivers_df[["driver_id", "behavior_profile"]],
        on="driver_id", how="left"
    ).dropna(subset=["behavior_profile"])

    features = [
        "harsh_brake_events", "harsh_accel_events",
        "idle_time_minutes", "speeding_km",
        "distance_km", "duration_hours",
        "max_speed_kmh", "avg_speed_kmh",
    ]
    X = df[features].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df["behavior_profile"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)

    feature_imp = pd.Series(clf.feature_importances_, index=features).sort_values(ascending=False)

    return clf, le, feature_imp, report, features


def predict_driver_safety(clf, le, features, new_data: dict) -> dict:
    """Score a new trip record."""
    X = pd.DataFrame([new_data])[features].fillna(0)
    proba = clf.predict_proba(X)[0]
    pred_class = le.inverse_transform([np.argmax(proba)])[0]
    proba_dict = {cls: round(float(p) * 100, 1) for cls, p in zip(le.classes_, proba)}
    return {"predicted_profile": pred_class, "probabilities": proba_dict}


# ── 2. Demand Forecasting (per city) ─────────────────────────────────

@st.cache_resource(show_spinner=False)
def train_demand_model(trips_df: pd.DataFrame):
    """
    Predict daily trip count for a given city using GBM.
    Features: day_of_week, month, year, is_weekend, city_encoded
    """
    df = trips_df.copy()
    df["date"] = pd.to_datetime(df["pickup_datetime"]).dt.date
    daily = df.groupby(["date", "pickup_city"]).size().reset_index(name="trip_count")
    daily["date"]    = pd.to_datetime(daily["date"])
    daily["dow"]     = daily["date"].dt.dayofweek
    daily["month"]   = daily["date"].dt.month
    daily["year"]    = daily["date"].dt.year
    daily["is_weekend"] = (daily["dow"] >= 5).astype(int)
    daily["day"]     = daily["date"].dt.day

    le_city = LabelEncoder()
    daily["city_enc"] = le_city.fit_transform(daily["pickup_city"])

    features = ["dow", "month", "year", "is_weekend", "day", "city_enc"]
    X = daily[features]
    y = daily["trip_count"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    gbm = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.08, random_state=42)
    gbm.fit(X_train, y_train)

    y_pred = gbm.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)

    return gbm, le_city, features, mae, r2


def forecast_demand(model, le_city, features, city: str, days_ahead: int = 30) -> pd.DataFrame:
    """Forecast daily demand for a city."""
    import datetime
    from datetime import date, timedelta

    today = date(2026, 7, 1)
    rows = []
    for i in range(1, days_ahead + 1):
        d = today + timedelta(days=i)
        try:
            city_enc = le_city.transform([city])[0]
        except ValueError:
            city_enc = 0
        rows.append({
            "date": d,
            "dow": d.weekday(),
            "month": d.month,
            "year": d.year,
            "is_weekend": int(d.weekday() >= 5),
            "day": d.day,
            "city_enc": city_enc,
        })
    X_future = pd.DataFrame(rows)[features]
    preds = model.predict(X_future)
    result = pd.DataFrame({"date": [r["date"] for r in rows], "predicted_trips": preds.clip(0)})
    return result


# ── 3. Revenue Forecasting (Prophet-like via SARIMA) ─────────────────

@st.cache_data(show_spinner=False)
def forecast_revenue_statsmodels(inv_df: pd.DataFrame, periods: int = 6):
    """
    6-month revenue forecast using Exponential Smoothing.
    Returns (historical_series, forecast_series, lower_ci, upper_ci).
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    monthly = inv_df.copy()
    monthly["month"] = monthly["invoice_date"].dt.to_period("M")
    ts = monthly.groupby("month")["total_amount_pkr"].sum().sort_index()

    # Ensure enough data
    if len(ts) < 12:
        ts_ext = ts.copy()
        for _ in range(12 - len(ts)):
            ts_ext[ts_ext.index[-1] + 1] = ts_ext.values[-1] * np.random.uniform(0.9, 1.1)
        ts = ts_ext.sort_index()

    model = ExponentialSmoothing(
        ts.values, trend="add", seasonal="add",
        seasonal_periods=min(12, len(ts) // 2),
        damped_trend=True,
    )
    fit = model.fit(optimized=True, use_brute=True)
    fc  = fit.forecast(periods)

    # Simple CI ±15%
    lower = fc * 0.85
    upper = fc * 1.15

    future_idx = pd.period_range(start=ts.index[-1] + 1, periods=periods, freq="M")
    return (
        pd.Series(ts.values, index=ts.index),
        pd.Series(fc, index=future_idx),
        pd.Series(lower, index=future_idx),
        pd.Series(upper, index=future_idx),
    )


# ── 4. Maintenance / Failure Prediction ──────────────────────────────

@st.cache_resource(show_spinner=False)
def train_maintenance_model(maint_df: pd.DataFrame, vehicles_df: pd.DataFrame):
    """
    Classify whether a vehicle needs maintenance soon (within 2 weeks).
    Features: vehicle age, odometer, days_since_last, maintenance_type_enc
    """
    from sklearn.linear_model import LogisticRegression

    df = maint_df.copy()
    df["maintenance_date"] = pd.to_datetime(df["maintenance_date"])
    df = df.sort_values(["vehicle_id", "maintenance_date"])
    df["days_since_last"] = df.groupby("vehicle_id")["maintenance_date"].diff().dt.days.fillna(90)

    veh = vehicles_df[["vehicle_id", "year", "odometer_km"]].copy().rename(columns={"odometer_km": "veh_odometer_km"})
    veh["vehicle_age"] = 2026 - veh["year"]
    df = df.merge(veh, on="vehicle_id", how="left")
    # Use the maint table's own odometer column
    if "odometer_km" not in df.columns:
        df["odometer_km"] = df["veh_odometer_km"].fillna(50000)

    le_type = LabelEncoder()
    df["type_enc"] = le_type.fit_transform(df["maintenance_type"])

    df["upcoming"] = (df["days_since_last"] < 14).astype(int)
    features = ["vehicle_age", "odometer_km", "days_since_last", "type_enc"]
    X = df[features].fillna(df[features].median())
    y = df["upcoming"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42)
    clf.fit(X_train, y_train)

    y_pred   = clf.predict(X_test)
    report   = classification_report(y_test, y_pred, output_dict=True)
    feat_imp = pd.Series(clf.feature_importances_, index=features).sort_values(ascending=False)

    return clf, le_type, features, report, feat_imp


# ── 5. Dynamic Pricing Recommender ────────────────────────────────────

@st.cache_resource(show_spinner=False)
def train_pricing_model(trips_df: pd.DataFrame):
    """
    Suggest optimal daily rate based on vehicle type, city, season, demand.
    """
    df = trips_df[trips_df["status"] == "Completed"].copy()
    df["month"]      = pd.to_datetime(df["pickup_datetime"]).dt.month
    df["dow"]        = pd.to_datetime(df["pickup_datetime"]).dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    le_city = LabelEncoder()
    le_type = LabelEncoder()
    df["city_enc"] = le_city.fit_transform(df["pickup_city"])
    df["type_enc"] = le_type.fit_transform(df["booking_type"])

    features = ["month", "dow", "is_weekend", "city_enc", "type_enc", "distance_km"]
    X = df[features].fillna(0)
    y = df["trip_fare_pkr"] / df["duration_days"].clip(0.1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.07, random_state=42)
    model.fit(X_train, y_train)

    mae = mean_absolute_error(y_test, model.predict(X_test))
    r2  = r2_score(y_test, model.predict(X_test))

    return model, le_city, le_type, features, mae, r2


def suggest_price(model, le_city, le_type, features,
                  month: int, dow: int, city: str, booking_type: str,
                  distance_km: float) -> float:
    try:
        city_enc = le_city.transform([city])[0]
    except ValueError:
        city_enc = 0
    try:
        type_enc = le_type.transform([booking_type])[0]
    except ValueError:
        type_enc = 0

    X = pd.DataFrame([{
        "month": month, "dow": dow, "is_weekend": int(dow >= 5),
        "city_enc": city_enc, "type_enc": type_enc, "distance_km": distance_km,
    }])[features]
    return float(model.predict(X)[0])


# ── 6. Anomaly Detection (Fuel) ────────────────────────────────────────

def detect_fuel_anomalies(fuel_df: pd.DataFrame) -> pd.DataFrame:
    """Flag trips where fuel efficiency deviates > 2 std from vehicle mean."""
    df = fuel_df.copy()
    veh_stats = df.groupby("vehicle_id")["fuel_efficiency_kmpl"].agg(["mean", "std"]).reset_index()
    veh_stats.columns = ["vehicle_id", "veh_mean_eff", "veh_std_eff"]
    df = df.merge(veh_stats, on="vehicle_id", how="left")
    df["veh_std_eff"] = df["veh_std_eff"].fillna(1)
    df["z_score"]     = (df["fuel_efficiency_kmpl"] - df["veh_mean_eff"]) / df["veh_std_eff"]
    df["is_anomaly"]  = df["z_score"].abs() > 2.0
    return df[df["is_anomaly"]].sort_values("z_score")
