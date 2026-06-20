import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path

# Setup page config
st.set_page_config(page_title="FCAES Operations Dashboard", page_icon="🛡️", layout="wide")

# Helper to load data
@st.cache_data(ttl=2) 
def load_data():
    db_path = Path("outputs/database.jsonl")
    if not db_path.exists():
        return pd.DataFrame()
        
    records = []
    with open(db_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
            
    df = pd.DataFrame(records)
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].astype(str).replace("nan", "")
        df.sort_values(by="timestamp", ascending=False, inplace=True)
    return df

df = load_data()

st.title("FCAES Operations Dashboard")
st.markdown("Facility compliance monitor and auditing system.")

if df.empty:
    st.warning("Database is currently empty. No detections logged yet.")
    st.stop()

tabA, tabB, tabC = st.tabs([
    "View A: Live Feed Monitor", 
    "View B: Alert Timeline Stream", 
    "View C: Historical Log & Export"
])

# -------------------------------------------------------------
# View A - Live Feed Monitor
# -------------------------------------------------------------
with tabA:
    st.header("Live Feed Monitor")
    st.markdown("Monitoring continuous feed from Zone 1. Compliance status is updated in real-time.")
    
    col_vid, col_status = st.columns([2, 1])
    
    with col_vid:
        annotated_videos = list(Path("outputs").glob("annotated_*.mp4"))
        
        if not annotated_videos:
            st.info("Simulation Video Feed Offline. No annotated videos found.")
        else:
            # Camera Switcher UI
            cam_names = [v.name for v in annotated_videos]
            
            if 'current_cam' not in st.session_state:
                st.session_state.current_cam = cam_names[0]
                
            col_sel1, col_sel2 = st.columns([3, 1])
            with col_sel1:
                selected_cam = st.selectbox("🎥 Select Camera Feed:", cam_names, index=cam_names.index(st.session_state.current_cam))
                st.session_state.current_cam = selected_cam
            with col_sel2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Random Feed"):
                    import random
                    st.session_state.current_cam = random.choice(cam_names)
                    st.rerun()
                    
            video_path = Path("outputs") / st.session_state.current_cam
            st.video(str(video_path))
            
    with col_status:
        st.subheader("Current Status")
        
        latest_event = df.iloc[0]
        tier = latest_event.get("severity", "LOW")
        rule = latest_event.get("behavior_class", "Unknown")
        
        if tier in ["CRIT", "HIGH"]:
            st.error(f"🚨 **ACTIVE ALERT TRIGGERED** 🚨\n\n**{tier}**: {rule}")
            st.warning("Immediate intervention required!")
            st.toast("CRITICAL ALERT DETECTED IN FEED!", icon="🚨")
        elif tier == "MED":
            st.warning(f"⚠️ **WARNING DETECTED**\n\n**{tier}**: {rule}")
        else:
            st.success("Area Secure. No critical violations detected.")
            
        st.divider()
        st.markdown("**Last Processed Event:**")
        st.json(latest_event.to_dict())

# -------------------------------------------------------------
# View B - Alert Timeline Stream
# -------------------------------------------------------------
with tabB:
    st.header("Alert Timeline Stream")
    st.markdown("Near-real-time chronological stream of compliance events.")
    
    display_df = df[["timestamp", "severity", "zone", "behavior_class", "event_description"]].copy()
    
    # Auto-refresh loop logic for Streamlit
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    if st.button("Refresh Stream"):
        st.rerun()

# -------------------------------------------------------------
# View C - Historical Log & Export
# -------------------------------------------------------------
with tabC:
    st.header("Historical Compliance Log")
    st.markdown("Audit system for all persisted records. Filter and export as needed.")
    
    col_f1, col_f2 = st.columns(2)
    
    # Filters
    with col_f1:
        selected_tiers = st.multiselect(
            "Filter by Severity Tier", 
            options=df["severity"].unique(),
            default=df["severity"].unique()
        )
        
    with col_f2:
        selected_rules = st.multiselect(
            "Filter by Behavior Class", 
            options=df["behavior_class"].unique(),
            default=df["behavior_class"].unique()
        )
        
    # Apply filters
    filtered_df = df[
        (df["severity"].isin(selected_tiers)) & 
        (df["behavior_class"].isin(selected_rules))
    ]
    
    st.dataframe(filtered_df, width='stretch')
    
    # Export Button (Downloads as CSV)
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export Filtered Log to CSV",
        data=csv_data,
        file_name='fcaes_compliance_audit_log.csv',
        mime='text/csv',
    )
