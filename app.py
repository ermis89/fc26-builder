import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide", page_title="FC26 Builder Pro")

# --- 1. ΦΟΡΤΩΣΗ & ΚΑΘΑΡΙΣΜΟΣ ΔΕΔΟΜΕΝΩΝ ---
@st.cache_data
def load_data():
    try:
        # Φόρτωση χωρίς headers αρχικά
        df_raw = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, low_memory=False)
        
        # --- A. LEVELS & AP ---
        levels_db = {}
        start_row = -1
        for i, row in df_raw.iterrows():
            if "Total so far" in row.astype(str).values:
                start_row = i + 1; break
        
        if start_row != -1:
            # Βρίσκουμε στήλες Level / Total AP
            headers = df_raw.iloc[start_row-1]
            c_lvl = -1; c_ap = -1
            for idx, val in enumerate(headers):
                if str(val).strip() == "Level": c_lvl = idx
                if "Total so far" in str(val): c_ap = idx
            
            for i in range(start_row, len(df_raw)):
                try:
                    l = int(float(df_raw.iloc[i, c_lvl]))
                    ap = int(float(df_raw.iloc[i, c_ap]))
                    levels_db[l] = ap
                except: break # Σταματάμε στο πρώτο κενό
        
        # --- B. ATTRIBUTES (Min/Max) ---
        attrs_db = []
        start_row_attr = -1
        for i, row in df_raw.iterrows():
            if "Attribute" in row.astype(str).values and "Min" in row.astype(str).values:
                start_row_attr = i + 1; break
        
        if start_row_attr != -1:
            # Βρίσκουμε στήλες
            headers = df_raw.iloc[start_row_attr-1]
            c_name = -1; c_min = -1; c_max = -1
            for idx, val in enumerate(headers):
                v = str(val).strip()
                if v == "Attribute": c_name = idx
                elif v == "Min": c_min = idx
                elif v == "Max": c_max = idx
            
            for i in range(start_row_attr, len(df_raw)):
                try:
                    name = str(df_raw.iloc[i, c_name]).strip()
                    mn = int(float(df_raw.iloc[i, c_min]))
                    mx = int(float(df_raw.iloc[i, c_max]))
                    # Φιλτράρισμα σκουπιδιών (π.χ. αριθμοί αντί για ονόματα)
                    if len(name) > 2 and name != "nan" and name != "Attribute":
                        attrs_db.append({"name": name, "min": mn, "max": mx})
                except: continue

        # --- C. ARCHETYPES SCANNING ---
        # Ψάχνουμε μοτίβα τύπου "Speedster (Marauder)"
        archetypes_struct = {}
        for r in range(len(df_raw)):
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c])
                # Regex για να βρούμε Name (Parent)
                match = re.search(r"(.+?)\s+\((.+?)\)", val)
                if match:
                    sub_arch = match.group(1).strip()
                    parent_arch = match.group(2).strip()
                    # Αποκλείουμε κείμενα που δεν είναι archetypes
                    if len(sub_arch) < 20 and "Column" not in parent_arch:
                        if parent_arch not in archetypes_struct:
                            archetypes_struct[parent_arch] = []
                        if sub_arch not in archetypes_struct[parent_arch]:
                            archetypes_struct[parent_arch].append(sub_arch)

        return levels_db, attrs_db, archetypes_struct

    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return {}, [], {}

levels, attributes, archetypes_map = load_data()

# --- 2. SIDEBAR (ΡΥΘΜΙΣΕΙΣ) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/EA_Sports_FC_logo.svg/1200px-EA_Sports_FC_logo.svg.png", width=100)
st.sidebar.header("⚙️ Setup Pro")

# Επιλογή Archetype (Βασισμένο σε αυτά που βρήκαμε στο CSV)
if archetypes_map:
    selected_class = st.sidebar.selectbox("Main Class", list(archetypes_map.keys()))
    # Sub-archetype (π.χ. Hotshot)
    selected_sub = st.sidebar.selectbox("Playstyle Focus", archetypes_map[selected_class])
else:
    st.sidebar.warning("Δεν βρέθηκαν Archetypes στο CSV.")
    selected_class = "Custom"

# Επιλογή Level
max_lvl_found = max(levels.keys()) if levels else 100
current_level = st.sidebar.number_input("Level", 1, 100, 100)
total_ap = levels.get(current_level, 160)

# --- 3. ΚΥΡΙΩΣ ΟΘΟΝΗ ---
st.title(f"FC26 Builder: {selected_class} ({selected_sub})")
st.markdown("---")

col_left, col_right = st.columns([0.6, 0.4])

# Logic Υπολογισμού Κόστους (FC Standard Logic)
# Αν δεν υπάρχει στο Excel, το βάζουμε εμείς εδώ:
def calculate_cost(current_val, min_val):
    diff = current_val - min_val
    # Κανόνας: +1 AP για τα πρώτα stats, +2 για τα υψηλά
    cost = 0
    for i in range(diff):
        stat_val = min_val + i
        if stat_val < 80: cost += 1
        elif stat_val < 90: cost += 2
        else: cost += 3 # Ακριβά stats πάνω από 90
    return cost

# --- SLIDERS ---
with col_left:
    st.subheader("📈 Attributes Distribution")
    
    user_costs = 0
    sliders_output = {}
    
    # Ομαδοποίηση (Αν μπορούσαμε, θα τα βάζαμε ανά κατηγορία Pace/Shooting)
    # Εδώ τα βάζουμε όλα σε λίστα
    for attr in attributes:
        # Εφαρμογή Archetype Logic (Dummy Modifier)
        # Εδώ θα μπορούσες να προσθέσεις: Αν είναι Marauder -> +5 Sprint Speed Min
        display_min = attr['min']
        display_max = attr['max']
        
        val = st.slider(
            f"{attr['name']} ({display_min}-{display_max})", 
            min_value=display_min, 
            max_value=display_max, 
            value=display_min,
            key=attr['name']
        )
        
        # Υπολογισμός κόστους
        this_cost = calculate_cost(val, display_min)
        user_costs += this_cost
        sliders_output[attr['name']] = val

# --- DASHBOARD ---
with col_right:
    st.subheader("📊 Build Summary")
    
    remaining = total_ap - user_costs
    
    # Card UI
    st.markdown(f"""
    <div style="background-color:#1e1e1e; padding:20px; border-radius:10px; border: 1px solid #333;">
        <h1 style="text-align:center; color:#32a852">{remaining}</h1>
        <p style="text-align:center;">Remaining AP</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.progress(min(user_costs / (total_ap + 1), 1.0))
    st.write(f"**Total Used:** {user_costs} / {total_ap}")
    
    if remaining < 0:
        st.error("⚠️ EXCEEDED BUDGET! Lower your stats.")
    else:
        st.success("✅ Build within limits.")

    st.markdown("### ⚡ Unlocked Playstyles")
    st.info("Select attributes to see if you unlock Playstyles.")
    # Εδώ θα βάλουμε τη λογική playstyle requirements αργότερα
    
    with st.expander("Debug Data (Τι διαβάσαμε από το CSV)"):
        st.write(archetypes_map)
