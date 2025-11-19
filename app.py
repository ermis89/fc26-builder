import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="FC26 Builder vFinal")

# --- LOGIC: Κόστος AP ---
def calculate_cost(base, current):
    if current <= base: return 0
    cost = 0
    for val in range(base, current):
        if val < 80: cost += 1
        elif val < 90: cost += 2
        else: cost += 3
    return cost

# --- DATA LOADER ---
@st.cache_data(show_spinner=False)
def load_data_clean():
    try:
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, dtype=str).fillna("")
    except:
        return {}, []

    # 1. LEVELS SCAN
    levels = {}
    c_lvl = -1; c_ap = -1
    
    # Ψάχνουμε headers
    for r in range(len(df)):
        for c in range(len(df.columns)):
            val = str(df.iloc[r, c]).strip()
            if val == "Level": c_lvl = c
            if "Total so far" in val: c_ap = c
        if c_lvl != -1 and c_ap != -1:
            # Διαβάζουμε από κάτω
            for i in range(r+1, len(df)):
                try:
                    l_str = str(df.iloc[i, c_lvl])
                    ap_str = str(df.iloc[i, c_ap])
                    if l_str.replace('.','').isdigit():
                        levels[int(float(l_str))] = int(float(ap_str))
                except: continue
            break
            
    # 2. ATTRIBUTES SCAN (Με Φίλτρο)
    attributes = []
    seen_names = set() 
    c_name = -1
    
    # Βρίσκουμε την "Acceleration"
    for r in range(len(df)):
        for c in range(len(df.columns)):
            if str(df.iloc[r, c]).strip() == "Acceleration":
                c_name = c
                c_min = c + 1
                c_max = c + 2
                
                if not df.iloc[r, c_min].replace('.','').isdigit():
                    c_min += 1; c_max += 1
                
                for i in range(r, len(df)):
                    name = str(df.iloc[i, c_name]).strip()
                    
                    if not name or name == "Attribute" or name == "nan": continue
                    if name.replace('.','').isdigit(): continue
                    if name in ["Totals", "Average", "Score"]: continue
                    if name in seen_names: continue
                    
                    try:
                        mn = int(float(df.iloc[i, c_min]))
                        mx = int(float(df.iloc[i, c_max]))
                        
                        if 10 <= mn <= 99:
                            attributes.append({"name": name, "min": mn, "max": mx})
                            seen_names.add(name)
                    except: continue
                break
        if c_name != -1: break

    return levels, attributes

# --- UI ---
st.sidebar.title("⚙️ FC26 Config")

if st.sidebar.button("🔄 Reload Data"):
    st.cache_data.clear()
    st.rerun()

levels_data, attrs_data = load_data_clean()

if not attrs_data:
    st.error("⚠️ Το αρχείο δεν φορτώθηκε σωστά. Πάτα Reload.")
else:
    # LEVEL
    st.sidebar.header("Level Selection")
    avail_levels = sorted(list(levels_data.keys()))
    
    if not avail_levels: avail_levels = [60] # Fallback

    default_idx = len(avail_levels) - 1
    sel_lvl = st.sidebar.selectbox("Player Level", avail_levels, index=default_idx)
    
    budget = levels_data.get(sel_lvl, 1569)
    st.sidebar.success(f"💰 **Total AP: {budget}**")

    # MAIN APP
    st.title(f"FC26 Pro Builder (Lvl {sel_lvl})")
    
    col1, col2 = st.columns([0.65, 0.35])
    
    total_spent = 0
    
    with col1:
        st.subheader("Attributes")
        c_a, c_b = st.columns(2)
        
        for i, attr in enumerate(attrs_data):
            target_col = c_a if i % 2 == 0 else c_b
            
            with target_col:
                val = st.slider(
                    attr['name'], 
                    attr['min'], 
                    attr['max'], 
                    attr['min'],
                    key=f"sl_{i}"
                )
                cost = calculate_cost(attr['min'], val)
                total_spent += cost
                if cost > 0:
                    st.caption(f"Cost: {cost}")

    with col2:
        remaining = budget - total_spent
        
        # HTML ΜΕΣΑ ΣΕ PYTHON STRING - ΑΥΤΟ ΕΙΝΑΙ ΤΟ ΣΩΣΤΟ
        st.markdown(f"""
            <div style="position: fixed; width: 300px; padding: 20px; 
                 background-color: #1E1E1E; border: 1px solid #444; 
                 border-radius: 10px; z-index: 999;">
                <h2 style="margin-top:0; color: #CCC;">Budget Status</h2>
                <h1 style="font-size: 48px; margin:0; color: {'#4CAF50' if remaining >= 0 else '#FF5252'}">
                    {remaining}
                </h1>
                <p>Remaining Points</p>
                <hr style="border-color: #444;">
                <p>Total Available: <b>{budget}</b></p>
                <p>Points Spent: <b>{total_spent}</b></p>
            </div>
        """, unsafe_allow_html=True)
