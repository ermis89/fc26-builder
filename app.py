import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="FC26 Builder Ultimate")

# --- ΚΑΝΟΝΕΣ ΚΟΣΤΟΥΣ FC (Αφού δεν υπάρχουν στο CSV ως τύποι) ---
def get_stat_cost(base_val, target_val):
    """Υπολογίζει το κόστος AP για να πας από το base στο target."""
    cost = 0
    for val in range(base_val, target_val):
        # Τυπικό κόστος FC:
        # 0-79: 1 AP
        # 80-89: 2 AP
        # 90-99: 3 AP (ή παραπάνω ανάλογα το Archetype)
        if val < 80:
            cost += 1
        elif val < 90:
            cost += 2
        else:
            cost += 3 # Ακριβά stats στο τέλος
    return cost

@st.cache_data
def load_full_data():
    try:
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, low_memory=False)
    except:
        return {}, [], []

    # 1. LEVELS & AP
    levels_map = {}
    start_row_lvl = -1
    for i, row in df.iterrows():
        if "Total so far" in row.astype(str).values:
            start_row_lvl = i + 1; break
            
    if start_row_lvl != -1:
        # Ψάχνουμε στήλες Level / Total so far
        headers = df.iloc[start_row_lvl-1]
        c_lvl = -1; c_ap = -1
        for idx, val in enumerate(headers):
            if str(val).strip() == "Level": c_lvl = idx
            if "Total so far" in str(val): c_ap = idx
            
        if c_lvl != -1 and c_ap != -1:
            for i in range(start_row_lvl, len(df)):
                try:
                    l = df.iloc[i, c_lvl]; ap = df.iloc[i, c_ap]
                    if pd.notna(l) and pd.notna(ap):
                        levels_map[int(float(l))] = int(float(ap))
                except: continue

    # 2. ATTRIBUTES (Min/Max)
    attributes_data = []
    start_row_attr = -1
    for i, row in df.iterrows():
        if "Attribute" in row.astype(str).values and "Min" in row.astype(str).values:
            start_row_attr = i + 1; break
            
    if start_row_attr != -1:
        headers = df.iloc[start_row_attr-1]
        c_name = -1; c_min = -1; c_max = -1
        for idx, val in enumerate(headers):
            v = str(val).strip()
            if v == "Attribute": c_name = idx
            elif v == "Min": c_min = idx
            elif v == "Max": c_max = idx
            
        if c_name != -1:
            for i in range(start_row_attr, len(df)):
                try:
                    name = str(df.iloc[i, c_name]).strip()
                    if name and name != "nan" and name != "Attribute" and len(name) > 2:
                        mn = int(float(df.iloc[i, c_min]))
                        mx = int(float(df.iloc[i, c_max]))
                        attributes_data.append({"name": name, "min": mn, "max": mx})
                except: continue

    # 3. PLAYSTYLES (ΝΕΟ)
    # Σαρώνουμε την 1η και 2η στήλη για λέξεις κλειδιά που μοιάζουν με Playstyles
    # (Εξαιρούμε τα Archetypes που έχουν παρένθεση)
    playstyles_found = []
    known_playstyles = ["Finesse", "Power", "Dead Ball", "Chip Shot", "Rapid", "Quick Step", "Relentless", "Trivela", "Technical", "Tiki Taka", "Pinged Pass", "Incisive Pass", "Long Ball", "Whipped Pass", "Bruiser", "Intercept", "Block", "Anticipate", "Acrobatic", "Aerial"]
    
    for i in range(len(df)):
        for col in [0, 1]: # Ψάχνουμε στις πρώτες 2 στήλες
            val = str(df.iloc[i, col]).strip()
            # Αν περιέχει γνωστό όνομα Playstyle
            if any(ps in val for ps in known_playstyles) and "(" not in val and "Select" not in val:
                if val not in playstyles_found:
                    playstyles_found.append(val)

    return levels_map, attributes_data, playstyles_found

# --- UI ---
levels, attrs, playstyles = load_full_data()

if not levels:
    st.error("⚠️ Φόρτωσε το αρχείο CSV!")
else:
    st.sidebar.title("⚽ FC26 Pro Builder")
    
    # Level Setup
    max_l = max(levels.keys())
    sel_level = st.sidebar.number_input("Level", 1, max_l, max_l)
    total_budget = levels.get(sel_level, 0)
    
    st.sidebar.markdown(f"### Budget: {total_budget} AP")
    st.sidebar.progress(0) # Placeholder
    
    # Playstyles Section (ΑΡΙΣΤΕΡΑ)
    st.sidebar.divider()
    st.sidebar.subheader("🛡️ Playstyles")
    selected_playstyles = []
    if playstyles:
        for ps in playstyles:
            if st.sidebar.checkbox(ps, key=ps):
                selected_playstyles.append(ps)
    else:
        st.sidebar.info("Δεν βρέθηκαν Playstyles στο CSV.")

    # Main Area
    st.title(f"Build Stats (Level {sel_level})")
    
    col1, col2 = st.columns([2, 1])
    
    total_cost = 0
    
    with col1:
        st.subheader("Attributes & Cost")
        
        for attr in attrs:
            min_v = attr['min']
            max_v = attr['max']
            
            # Slider
            val = st.slider(
                f"{attr['name']}", 
                min_value=min_v, 
                max_value=max_v, 
                value=min_v
            )
            
            # Κόστος
            cost = get_stat_cost(min_v, val)
            total_cost += cost
            
            # Εμφάνιση κόστους δίπλα
            if cost > 0:
                st.caption(f"⬆️ Cost: {cost} AP (Gained +{val - min_v})")

    with col2:
        st.markdown("### 📊 Summary")
        
        remaining = total_budget - total_cost
        
        # Card Design
        st.markdown(f"""
        <div style="border: 1px solid #444; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: {'#4CAF50' if remaining >= 0 else '#F44336'}">{remaining}</h2>
            <p>Remaining AP</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.write(f"**Total Budget:** {total_budget}")
        st.write(f"**Spent:** {total_cost}")
        
        if selected_playstyles:
            st.write("---")
            st.write("**Active Playstyles:**")
            for ps in selected_playstyles:
                st.markdown(f"- 🛡️ {ps}")
                # Εδώ θα μπορούσαμε να βάλουμε warnings αν δεν πιάνεις τα stats
                # π.χ. if ps == "Rapid" and user_speed < 75: ...
