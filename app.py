import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Horse Racing Projection Tool (AU)", layout="wide")
st.title("🏇 Horse Racing Projection Tool (Australia BM Ready)")

uploaded_file = st.file_uploader("Upload race CSV", type=["csv"])

def clean_cols(df):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df

def require_columns(df, required):
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("Missing required columns:")
        st.write(missing)
        st.info("Columns found in your file:")
        st.write(list(df.columns))
        st.stop()

def to_numeric(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# ---------------- Scoring components ----------------

def recent_form_score(df):
    # Lower finish is better
    df["form_score"] = (10 - df["finish_position"]).clip(lower=0)
    return df

def pace_score(df):
    # Early vs late blend
    df["pace_score"] = df["early_speed"] * 0.45 + df["late_speed"] * 0.55
    return df

def class_bm_score(df):
    """
    In BM racing, lower BM in stronger races is usually tougher,
    but within a field, we can treat BM as a quality indicator.
    Here we score relative to field average.
    """
    bm_avg = df["bm"].mean()
    df["bm_score"] = (df["bm"] - bm_avg) * 0.8  # tweakable
    return df

def weight_score(df):
    """
    Penalize weight above field average; reward below average.
    """
    w_avg = df["weight"].mean()
    df["weight_score"] = (w_avg - df["weight"]) * 1.2  # 1kg ~= small impact
    return df

def freshness_score(df):
    """
    Simple freshness curve:
    - Too quick back-up (<=5 days): small penalty
    - Sweet spot (10–28 days): bonus
    - Very long break (>=60): penalty
    """
    d = df["days_since"].clip(lower=0)

    score = np.zeros(len(df))

    # quick backup penalty
    score += np.where(d <= 5, -2.0, 0.0)

    # sweet spot bonus
    score += np.where((d >= 10) & (d <= 28), 2.0, 0.0)

    # moderate break neutral (29-59)
    score += np.where((d >= 29) & (d <= 59), 0.5, 0.0)

    # long break penalty
    score += np.where(d >= 60, -1.5, 0.0)

    df["freshness_score"] = score
    return df

def distance_score(df):
    """
    Reward being close to preferred distance.
    """
    diff = (df["distance"] - df["preferred_distance"]).abs()
    df["distance_score"] = (10 - (diff / 200)).clip(lower=-5, upper=10)
    return df

def track_score(df):
    """
    Simple surface suitability:
    Exact match = bonus
    Adjacent (Good<->Soft, Soft<->Heavy) = small bonus
    Mismatch (Good vs Heavy) = penalty
    """
    order = {"good": 0, "soft": 1, "heavy": 2}

    tc = df["track_condition"].astype(str).str.lower()
    ps = df["preferred_surface"].astype(str).str.lower()

    tc_i = tc.map(order)
    ps_i = ps.map(order)

    # if unknown labels, set neutral
    valid = tc_i.notna() & ps_i.notna()
    delta = (tc_i - ps_i).abs()

    score = np.zeros(len(df))
    score = np.where(valid & (delta == 0), 2.0, score)
    score = np.where(valid & (delta == 1), 0.5, score)
    score = np.where(valid & (delta >= 2), -1.5, score)

    df["track_score"] = score
    return df

def compute_projection(df):
    """
    Weighted blend. You can tweak these weights anytime.
    """
    df["projection_score"] = (
        df["form_score"] * 1.2 +
        df["pace_score"] * 0.35 +
        df["bm_score"] * 0.6 +
        df["weight_score"] * 1.0 +
        df["freshness_score"] * 1.0 +
        df["distance_score"] * 0.8 +
        df["track_score"] * 1.0
    )
    return df

# ---------------- Main ----------------

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = clean_cols(df)

    required = [
        "horse_id","finish_position","early_speed","late_speed",
        "bm","weight","days_since","distance","preferred_distance",
        "track_condition","preferred_surface"
    ]
    require_columns(df, required)

    df = to_numeric(df, ["finish_position","early_speed","late_speed","bm","weight","days_since","distance","preferred_distance"])
    df = df.dropna(subset=["horse_id","finish_position","early_speed","late_speed","bm","weight","days_since","distance","preferred_distance"])

    st.subheader("📄 Data loaded")
    st.dataframe(df)

    df = recent_form_score(df)
    df = pace_score(df)
    df = class_bm_score(df)
    df = weight_score(df)
    df = freshness_score(df)
    df = distance_score(df)
    df = track_score(df)
    df = compute_projection(df)

    st.subheader("🏆 Rankings (BM-ready)")
    show_cols = [
        "horse_id","projection_score",
        "form_score","pace_score","bm_score","weight_score",
        "freshness_score","distance_score","track_score"
    ]
    st.dataframe(df.sort_values("projection_score", ascending=False)[show_cols])

