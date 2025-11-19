import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="FC26 Builder Pro")

# --- 1. LOGIC ---
def calculate_cost(base, current):
    if current <= base: return 0
    cost = 0
    for val in range(base, current):
        if val < 80: cost += 1
        elif val < 90: cost += 2
        else: cost += 3
    return cost

# Κατηγοριοποίηση για το Radar Chart
CATEGORIES = {
    "Pace": ["Acceleration", "SprintSpeed"],
    "Shooting": ["Finishing", "ShotPower", "LongShots", "Volleys", "Penalties", "AttackPositioning"],
    "Passing": ["Vision", "Crossing", "FKAccuracy", "ShortPassing", "LongPassing", "Curve"],
    "Dribbling": ["Agility", "Balance", "Reactions", "BallControl", "Dribbling", "Composure"],
    "Defending": ["Interceptions", "Heading Accuracy", "DefAwareness", "StandingTackle", "SlidingTackle"],
    "Physical": ["Jumping", "Stamina", "Strength", "Aggression"]
}

# --- 2. DATA LOADER ---
@st.cache_data(show_spinner=False)
def load_data_v2():
    try:
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, dtype=str).fillna("")
    except:
        return {}, []

    # Levels
    levels = {}
    c_lvl = -1; c_ap = -1
    for r in range(len(df)):
        for c in range(len(df.columns)):
            val = str(df.iloc[r, c]).strip()
            if val == "Level": c_lvl = c
            if "Total so far" in val: c_ap = c
        if c_lvl != -1:
            for i in range(r+1, len(df)):
                try:
                    l = int(float(df.iloc[i, c_lvl]))
                    ap = int(float(df.iloc[i, c_ap]))
                    levels[l] = ap
                except: continue
            break
            
    # Attributes
    attributes = []
    seen = set()
    c_name = -1
    
    for r in range(len(df)):
        for c in range(len(df.columns)):
            if str(df.iloc[r, c]).strip() == "Acceleration":
                c_name = c
                c_min = c+1; c_max = c+2
                if not df.iloc[r, c_min].replace('.','').isdigit(): c_min+=1; c_max+=1
                
                for i in range(r, len(df)):
                    name = str(df.iloc[i, c_name]).strip()
                    if not name or name in ["Attribute", "nan", "Totals"] or name.replace('.','').isdigit(): continue
                    if name in seen: continue
                    try:
                        mn = int(float(df.iloc[i, c_min]))
                        mx = int(float(df.iloc[i, c_max]))
                        if 10 <= mn <= 99:
                            attributes.append({"name": name, "min": mn, "max": mx, "cat": "Other"})
                            seen.add(name)
                    except: continue
                break
        if c_name != -1: break
    
    # Assign Categories
    for attr in attributes:
        for cat, keywords in CATEGORIES.items():
            if attr['name'] in keywords:
                attr['cat'] = cat
                break

    return levels, attributes

# --- 3. UI ---
levels_data, attrs_data = load_data_v2()

# Sidebar
st.sidebar.title("⚙️ Player Config")
if st.sidebar.button("🔄 Reset / Reload"):
    st.cache_data.clear()
    st.rerun()

if attrs_data:
    # Level Selector
    lvls = sorted(list(levels_data.keys()))
    if not lvls: lvls = [60]
    sel_lvl = st.sidebar.selectbox("Level", lvls, index=len(lvls)-1)
    budget = levels_data.get(sel_lvl, 1569)

    # Main Layout
    st.title("FC26 Pro Builder")
    
    col_controls, col_visuals = st.columns([0.55, 0.45])
    
    user_vals = {}
    total_spent = 0

    with col_controls:
        st.subheader("🛠️ Build Attributes")
        # Tabs για να μοιάζει με Proxi
        tabs = st.tabs(["PAC/SHO", "PAS/DRI", "DEF/PHY"])
        
        # Group attributes
        grouped = {c: [] for c in CATEGORIES}
        for a in attrs_data:
            if a['cat'] in grouped: grouped[a['cat']].append(a)
            else: grouped.setdefault("Other", []).append(a)

        # Tab 1
        with tabs[0]:
            st.markdown("### Pace & Shooting")
            for cat in ["Pace", "Shooting"]:
                st.caption(f"--- {cat} ---")
                for attr in grouped.get(cat, []):
                    v = st.slider(attr['name'], attr['min'], attr['max'], attr['min'], key=attr['name'])
                    c = calculate_cost(attr['min'], v)
                    total_spent += c
                    user_vals[attr['name']] = v

        # Tab 2
        with tabs[1]:
            st.markdown("### Passing & Dribbling")
            for cat in ["Passing", "Dribbling"]:
                st.caption(f"--- {cat} ---")
                for attr in grouped.get(cat, []):
                    v = st.slider(attr['name'], attr['min'], attr['max'], attr['min'], key=attr['name'])
                    c = calculate_cost(attr['min'], v)
                    total_spent += c
                    user_vals[attr['name']] = v

        # Tab 3
        with tabs[2]:
            st.markdown("### Defense & Physical")
            for cat in ["Defending", "Physical"]:
                st.caption(f"--- {cat} ---")
                for attr in grouped.get(cat, []):
                    v = st.slider(attr['name'], attr['min'], attr['max'], attr['min'], key=attr['name'])
                    c = calculate_cost(attr['min'], v)
                    total_spent += c
                    user_vals[attr['name']] = v

    with col_visuals:
        # Sticky Panel
        remaining = budget - total_spent
        
        # 1. Budget Card
        st.markdown(f"""
        <div style="background: #111; border:1px solid #333; padding:15px; border-radius:10px; text-align:center; margin-bottom: 20px;">
            <h2 style="color:{'#4CAF50' if remaining>=0 else '#F44336'}; margin:0;">{remaining} AP</h2>
            <span style="color:#888">Remaining Budget</span>
        </div>
        """, unsafe_allow_html=True)

        # 2. RADAR CHART (Η "Μαγεία")
        # Υπολογισμός μέσων όρων ανά κατηγορία
        radar_vals = []
        radar_cats = []
        
        for cat, items in CATEGORIES.items():
            vals = [user_vals.get(x, 0) for x in items if x in user_vals]
            if vals:
                avg = sum(vals) / len(vals)
                radar_vals.append(avg)
                radar_cats.append(cat)
        
        # Κλείσιμο του κύκλου
        if radar_vals:
            radar_vals.append(radar_vals[0])
            radar_cats.append(radar_cats[0])

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=radar_vals,
                theta=radar_cats,
                fill='toself',
                name='My Build',
                line_color='#00ffcc'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[40, 100])),
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white")
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 3. Playstyles (Placeholder για το μέλλον)
        with st.expander("Active Playstyles"):
            st.info("Select your attributes to unlock styles (Logic coming soon)")

else:
    st.error("CSV not found. Upload & Reload.")
