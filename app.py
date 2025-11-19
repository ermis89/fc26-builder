import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide", page_title="FC26 Builder Final")

# --- 1. LOGIC ENGINE (Κόστος AP) ---
def calculate_cost(base, current):
    if current <= base: return 0
    cost = 0
    for val in range(base, current):
        if val < 80: cost += 1
        elif val < 90: cost += 2
        else: cost += 3
    return cost

# --- 2. DATA LOADER (ΣΑΡΩΣΗ ΜΕΧΡΙ ΤΕΛΟΣ) ---
@st.cache_data
def load_data_final():
    try:
        # Διαβάζουμε όλο το αρχείο, ΟΧΙ μόνο τις πρώτες γραμμές
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, dtype=str).fillna("")
    except:
        return {}, []

    # --- LEVELS ---
    levels = {}
    # Ψάχνουμε τη στήλη Level & Total so far
    c_lvl = -1; c_ap = -1
    
    # Σάρωση για headers
    for r in range(len(df)):
        for c in range(len(df.columns)):
            val = str(df.iloc[r, c]).strip()
            if val == "Level": c_lvl = c
            if "Total so far" in val: c_ap = c
        if c_lvl != -1 and c_ap != -1:
            # Βρήκαμε τους headers, διαβάζουμε από κάτω
            start_r = r + 1
            for i in range(start_r, len(df)):
                try:
                    l_str = str(df.iloc[i, c_lvl])
                    ap_str = str(df.iloc[i, c_ap])
                    if l_str.replace('.','').isdigit():
                        l = int(float(l_str))
                        ap = int(float(ap_str))
                        levels[l] = ap
                except: continue
            break
    
    # ΔΙΟΡΘΩΣΗ ΓΙΑ MAX LEVEL 60
    # Αν το CSV σταματάει στο 50, συμπληρώνουμε εμείς
    max_l_found = max(levels.keys()) if levels else 0
    if max_l_found < 60:
        last_ap = levels.get(max_l_found, 0)
        for x in range(max_l_found + 1, 61):
            last_ap += 25 # Υπόθεση: +25 AP ανά level μετά το 50 (Adjustable)
            levels[x] = last_ap
    
    # Manual Override για το Level 60 που ζήτησες
    levels[60] = 1569

    # --- ATTRIBUTES (Η ΜΕΓΑΛΗ ΔΙΟΡΘΩΣΗ) ---
    attributes = []
    c_name = -1
    
    # Βρίσκουμε τη στήλη "Acceleration" (Άγκυρα)
    for r in range(len(df)):
        for c in range(len(df.columns)):
            if str(df.iloc[r, c]).strip() == "Acceleration":
                c_name = c
                # Υποθέτουμε Min/Max είναι δεξιά
                c_min = c + 1
                c_max = c + 2
                # Αν πέσουμε σε κενό, ψάχνουμε παραδίπλα
                if not df.iloc[r, c_min].replace('.','').isdigit():
                    c_min += 1; c_max += 1
                
                # Σαρώνουμε ΜΕΧΡΙ ΤΟ ΤΕΛΟΣ ΤΟΥ ΑΡΧΕΙΟΥ (Row 300+)
                for i in range(r, len(df)):
                    name = str(df.iloc[i, c_name]).strip()
                    
                    # Αγνοούμε κενά, headers, ή σκουπίδια
                    if not name or name == "Attribute" or name == "nan": continue
                    
                    # Προσπαθούμε να διαβάσουμε αριθμούς
                    try:
                        mn_str = str(df.iloc[i, c_min])
                        mx_str = str(df.iloc[i, c_max])
                        
                        if mn_str.replace('.','').isdigit() and mx_str.replace('.','').isdigit():
                            mn = int(float(mn_str))
                            mx = int(float(mx_str))
                            
                            # Φίλτρο: Να είναι λογικά νούμερα (π.χ. όχι ημερομηνίες)
                            if 20 <= mn <= 99 and 20 <= mx <= 99:
                                attributes.append({"name": name, "min": mn, "max": mx})
                    except: continue
                break # Σταματάμε την εξωτερική αναζήτηση αφού βρήκαμε τη στήλη
        if c_name != -1: break

    return levels, attributes

# --- 3. UI ---
levels_data, attrs_data = load_data_final()

if not attrs_data:
    st.error("⚠️ Δεν βρέθηκαν Attributes. Το αρχείο πρέπει να έχει τη λέξη 'Acceleration'.")
else:
    # Sidebar
    st.sidebar.header("🎚️ Player Settings")
    
    # LEVEL SELECTOR (Max 60)
    # Χρησιμοποιούμε selectbox για να παίρνουμε ακριβώς τα AP από τον πίνακα
    avail_levels = sorted(list(levels_data.keys()))
    if not avail_levels: avail_levels = list(range(1, 61))
    
    selected_lvl = st.sidebar.selectbox("Level", avail_levels, index=len(avail_levels)-1)
    
    # AP Calculation
    total_ap = levels_data.get(selected_lvl, 1569)
    
    st.sidebar.divider()
    st.sidebar.metric("Total AP Available", total_ap)
    
    # Main Stats
    st.title(f"FC26 Builder (Level {selected_lvl})")
    st.write(f"Loaded {len(attrs_data)} attributes from CSV.")
    
    col1, col2 = st.columns([2, 1])
    
    spent_ap = 0
    
    with col1:
        # Εμφάνιση σε 2 στήλες μέσα στο panel
        sub_c1, sub_c2 = st.columns(2)
        
        for idx, attr in enumerate(attrs_data):
            # Μοιράζουμε τα stats αριστερά-δεξιά
            target_col = sub_c1 if idx % 2 == 0 else sub_c2
            
            with target_col:
                val = st.slider(
                    f"{attr['name']}", 
                    min_value=attr['min'], 
                    max_value=attr['max'], 
                    value=attr['min'],
                    key=f"s_{idx}"
                )
                cost = calculate_cost(attr['min'], val)
                spent_ap += cost
                if cost > 0:
                    st.caption(f"Cost: {cost}")

    with col2:
        rem = total_ap - spent_ap
        
        st.markdown(f"""
            <div style='text-align: center; padding: 20px; border: 2px solid #444; border-radius: 10px; background-color: #262730;'>
                <h2 style='margin:0; color: #aaa;'>REMAINING AP</h2>
                <h1 style='margin:0; font-size: 3em; color: {"#4CAF50" if rem >= 0 else "#FF5252"}'>{rem}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.progress(min(spent_ap / (total_ap + 0.1), 1.0))
        st.write(f"**Spent:** {spent_ap} / {total_ap}")
