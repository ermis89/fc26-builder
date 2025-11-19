import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="FC26 Builder Ultimate")

# --- ΒΟΗΘΗΤΙΚΗ ΣΥΝΑΡΤΗΣΗ ΚΟΣΤΟΥΣ ---
def get_stat_cost(current_val, min_val):
    """Υπολογίζει πόσα AP κοστίζει η αύξηση"""
    if current_val <= min_val: return 0
    cost = 0
    for val in range(min_val, current_val):
        if val < 80: cost += 1
        elif val < 90: cost += 2
        else: cost += 3
    return cost

@st.cache_data
def load_all_data_unfiltered():
    try:
        # Διαβάζουμε όλο το CSV ως κείμενο για να μην χάσουμε τίποτα
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, dtype=str)
    except:
        return {}, [], []

    # 1. LEVELS (Όπως και πριν)
    levels_map = {}
    # Ψάχνουμε "Total so far"
    start_row_lvl = -1
    for i, row in df.iterrows():
        if "Total so far" in row.values:
            start_row_lvl = i + 1; break
            
    if start_row_lvl != -1:
        # Βρίσκουμε στήλες
        headers = df.iloc[start_row_lvl-1]
        c_lvl = -1; c_ap = -1
        for idx, val in enumerate(headers):
            if str(val).strip() == "Level": c_lvl = idx
            if "Total so far" in str(val): c_ap = idx
            
        if c_lvl != -1 and c_ap != -1:
            for i in range(start_row_lvl, len(df)):
                try:
                    l = float(df.iloc[i, c_lvl])
                    ap = float(df.iloc[i, c_ap])
                    levels_map[int(l)] = int(ap)
                except: continue

    # 2. ATTRIBUTES (Min/Max)
    attributes_data = []
    start_row_attr = -1
    for i, row in df.iterrows():
        if "Attribute" in row.values and "Min" in row.values:
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
                    if len(name) > 2 and name != "Attribute" and name != "nan":
                        mn = int(float(df.iloc[i, c_min]))
                        mx = int(float(df.iloc[i, c_max]))
                        attributes_data.append({"name": name, "min": mn, "max": mx})
                except: continue

    # 3. PLAYSTYLES - Η ΜΕΓΑΛΗ ΑΛΛΑΓΗ
    # Δεν φιλτράρουμε με λέξεις. Παίρνουμε τα πάντα από την 1η στήλη
    # που δεν είναι Archetype (δεν έχει παρένθεση) και δεν είναι Header.
    playstyles_found = []
    
    # Συνήθως τα Playstyles ξεκινάνε μετά τη γραμμή 25
    for i in range(20, len(df)):
        val = str(df.iloc[i, 0]).strip() # Στήλη Α (Όνομα)
        req_val = str(df.iloc[i, 2]).strip() # Στήλη C (Συχνά έχει το Requirement π.χ. 80)
        
        # Κανόνες για να μην πάρουμε σκουπίδια:
        if (len(val) > 3 and          # Να έχει μήκος
            val != "nan" and          # Να μην είναι κενό
            "(" not in val and        # Να μην είναι Archetype π.χ. Hotshot (Magician)
            "Select" not in val and   # Να μην είναι οδηγία
            "Check Playstyle" not in val):
            
            # Προσπάθεια να βρούμε την απαίτηση (Αν η στήλη C είναι αριθμός)
            requirement = ""
            if req_val.replace('.', '', 1).isdigit():
                requirement = f"(Req: {req_val})"
            
            playstyles_found.append({"name": val, "req": requirement})

    return levels_map, attributes_data, playstyles_found

# --- UI ---
levels, attrs, playstyles_list = load_all_data_unfiltered()

if not levels:
    st.error("⚠️ Πρόβλημα με το αρχείο CSV. Βεβαιώσου ότι ανέβηκε σωστά.")
else:
    # Setup
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/EA_Sports_FC_logo.svg/1200px-EA_Sports_FC_logo.svg.png", width=100)
    st.sidebar.title("FC26 Builder")
    
    # Levels
    max_l = max(levels.keys())
    sel_level = st.sidebar.number_input("Level", 1, max_l, max_l)
    total_budget = levels.get(sel_level, 1000)
    st.sidebar.markdown(f"### 💰 Budget: {total_budget}")
    
    # --- PLAYSTYLES SECTION (ΤΩΡΑ ΘΑ ΤΑ ΔΕΙΣ) ---
    st.sidebar.divider()
    st.sidebar.subheader(f"🛡️ Playstyles ({len(playstyles_list)})")
    
    selected_ps = []
    
    if not playstyles_list:
        st.sidebar.error("Δεν βρέθηκαν Playstyles στη Στήλη A.")
    else:
        # Εμφάνιση όλων
        for ps in playstyles_list:
            label = f"{ps['name']} {ps['req']}"
            if st.sidebar.checkbox(label, key=ps['name']):
                selected_ps.append(ps['name'])

    # --- MAIN AREA ---
    st.title(f"Build Level {sel_level}")
    
    col1, col2 = st.columns([2, 1])
    
    total_spent = 0
    
    with col1:
        st.subheader("Attributes")
        # Sliders
        for attr in attrs:
            val = st.slider(attr['name'], attr['min'], attr['max'], attr['min'])
            cost = get_stat_cost(val, attr['min'])
            total_spent += cost
            if cost > 0:
                st.caption(f"Cost: {cost} AP")

    with col2:
        remaining = total_budget - total_spent
        
        st.markdown(f"""
        <div style="background-color: #222; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #444;">
            <h1 style="color: {'#4CAF50' if remaining >= 0 else '#ff4444'}; margin:0;">{remaining}</h1>
            <p style="margin:0; color: #aaa;">Remaining AP</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.write("**Active Playstyles:**")
        for p in selected_ps:
            st.success(p)
            
        # DEBUGGING (ΓΙΑ ΝΑ ΔΕΙΣ ΤΙ ΔΙΑΒΑΖΕΙ)
        with st.expander("🔍 Debug Data (Τι βλέπει ο κώδικας)"):
            st.write("Raw Playstyles Found:", playstyles_list)
            st.write("Attributes Found:", len(attrs))
