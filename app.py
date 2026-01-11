import streamlit as st
import requests

st.set_page_config(page_title="Live Race Loader", layout="wide")
st.title("🏇 Live Race Projection Tool (API test)")

api_key = st.text_input("Paste your Punting Form API key here", type="password")
meeting_id = st.text_input("Meeting ID")
race_no = st.number_input("Race number (0 = whole meeting)", min_value=0, max_value=20, value=0)

FORM_URL = "https://api.puntingform.com.au/v2/form/form"

def call_pf_form(api_key: str, meeting_id: str, race_no: int):
    params = {"meetingId": meeting_id, "raceNumber": race_no}

    # Try the most common header styles (we'll see which one works)
    headers_options = [
        {"x-api-key": api_key},
        {"Authorization": f"Bearer {api_key}"},
        {"Authorization": api_key},
    ]

    last_err = None
    for headers in headers_options:
        try:
            r = requests.get(FORM_URL, params=params, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.json(), headers
            last_err = (r.status_code, r.text)
        except Exception as e:
            last_err = str(e)

    raise RuntimeError(f"API call failed. Last error: {last_err}")

if st.button("Test API"):
    if not api_key or not meeting_id:
        st.error("Paste your API key AND enter a meeting ID.")
        st.stop()

    try:
        data, used_headers = call_pf_form(api_key, meeting_id.strip(), int(race_no))
        st.success(f"✅ Connected! Using headers: {list(used_headers.keys())}")
        st.json(data)  # shows returned JSON so we can map it into your projection model
    except Exception as e:
        st.error(str(e))
