import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Horse Racing Projection Tool", layout="wide")
st.title("🏇 Horse Racing Projection Tool")

uploaded_file = st.file_uploader("Upload race CSV", type=["csv"])

def clean_cols(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df

def recent_form_score(df):
    df['recent_avg_finish'] = df.groupby('horse_id')['finish_position'] \
        .rolling(3, min_periods=1).mean().reset_index(0, drop=True)
    df['form_score'] = (10 - df['recent_avg_finish']).clip(lower=0)
    return df

def compute_projection(df):
    df['projection_score'] = (
        df['form_score'] * 0.6 +
        (df['early_speed'] * 0.4 + df['late_speed'] * 0.6) * 0.4
    )
    return df

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = clean_cols(df)

    required = ['horse_id','finish_position','early_speed','late_speed']
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error("Missing columns:")
        st.write(missing)
        st.write("Found columns:")
        st.write(list(df.columns))
        st.stop()

    df = recent_form_score(df)
    df = compute_projection(df)

    st.subheader("🏆 Rankings")
    st.dataframe(
        df.sort_values("projection_score", ascending=False)
        [['horse_id','projection_score']]
    )
