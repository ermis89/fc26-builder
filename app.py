import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="FC26 Pro Builder Ultimate")

# --- 1. ΤΑ ΔΕΔΟΜΕΝΑ ΤΟΥ FC26 (Hardcoded για σιγουριά) ---
# Επειδή το CSV δεν μας δίνει τη λογική, την ορίζουμε εδώ.
# ΑΥΤΟ ΕΙΝΑΙ ΠΟΥ ΕΛΕΙΠΕ:
FC_LOGIC = {
    "ARCHETYPES": {
        "Magician": {"focus": "Dribbling/Passing", "bonus": {"Agility": 85, "Vision": 84, "Dribbling": 86}},
        "Marauder": {"focus": "Pace/Physical", "bonus": {"Sprint Speed": 82, "Acceleration": 84, "Strength": 75}},
        "Finisher": {"focus": "Shooting", "bonus": {"Finishing": 88, "Shot Power": 85, "Volleys": 80}},
        "Creator":  {"focus": "Passing", "bonus": {"Vision": 86, "Long Passing": 84, "Short Passing": 88}},
        "Spark":    {"focus": "Agility", "bonus": {"Agility": 88, "Balance": 86, "Acceleration": 85}},
        "Boss":     {"focus": "Defense", "bonus": {"Interceptions": 85, "Stand Tackle": 86, "Strength": 88}},
        "Engine":   {"focus": "Work Rate", "bonus": {"Stamina": 90, "Reactions": 85, "Interceptions": 80}}
    },
    "LEVELS_AP": { 
        # Τυπικός πίνακας Level -> AP (Αν το CSV αποτύχει)
        10: 224, 25: 435, 50: 834, 75: 1050, 100: 1269
    },
    "PLAYSTYLES": [
        "Finesse Shot", "Power Header", "Dead Ball", "Chip Shot", 
        "Rapid", "Quick Step", "Relentless", "Trivela", "Technical"
    ]
}

@st.cache_data
def load_basic_stats():
    # Φορτώνουμε ΜΟΝΟ τα ονόματα των Attributes από το CSV για να είναι σωστή η σειρά
    try:
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None)
        attributes = []
        start_row = -1
        # Ψάχνουμε το Attribute table
        for i, row in df.iterrows():
            if "Attribute" in row.values and "Min" in row.values:
                start_row = i + 1; break
        
        if start_row != -1:
            # Βρίσκουμε τη στήλη με τα ονόματα
            header = df.iloc[start_row-1]
            c_name = -1; c_min = -1
            for idx, val in enumerate(header):
                if str(val).strip() == "Attribute": c_name = idx
                if str(val).strip() == "Min": c_min = idx

            for i in range(start_row, len(df)):
                val = str(df.iloc[i, c_name]).strip()
                min_v = df.iloc[i, c_min]
                if val and val != "nan" and val != "Attribute" and len(val) > 2:
                    # Καθαρισμός τιμής Min
                    try: base_min = int(float(min_v))
                    except: base_min = 60
                    attributes.append({"name": val, "base_min": base_min})
        return attributes
    except:
        # Fallback αν δεν βρεθεί τίποτα
        return [{"name": "Acceleration", "base_min": 60}, {"name": "Sprint Speed", "base_min": 60}, 
                {"name": "Finishing", "base_min": 60}, {"name": "Shot Power", "base_min": 60},
                {"name": "Agility", "base_min": 60}, {"name": "Balance", "base_min": 60}]

attributes_list = load_basic_stats()

# --- 2. UI SETUP ---
st.sidebar.title("⚽ FC26 Pro Setup")

# A. ΕΠΙΛΟΓΗ ARCHETYPE (Πλέον λειτουργεί!)
selected_arch_name = st.sidebar.selectbox("Επίλεξε Archetype", list(FC_LOGIC["ARCHETYPES"].keys()))
arch_data = FC_LOGIC["ARCHETYPES"][selected_arch_name]

st.sidebar.info(f"**Focus:** {arch_data['focus']}")

# B. LEVEL & AP
user_level = st.sidebar.slider("Level Παίκτη", 1, 100, 100)
# Υπολογισμός AP (Απλοποιημένος ή από CSV)
total_ap = 100 + (user_level * 11) # Fallback logic
st.sidebar.markdown(f"# 💰 AP: {total_ap}")

# --- 3. MAIN SCREEN ---
st.title(f"Build: {selected_arch_name} (Lvl {user_level})")

col1, col2, col3 = st.columns([1, 1, 0.8])

user_costs = 0
user_selections = {}

# --- ΚΑΤΗΓΟΡΙΕΣ STATS (ΓΙΑ ΝΑ ΜΗΝ ΕΙΝΑΙ ΧΥΜΑ) ---
# Ομαδοποιούμε τα stats για να μοιάζει με το παιχνίδι
categories = {
    "Pace": ["Acceleration", "Sprint Speed", "SprintSpeed"],
    "Shooting": ["Finishing", "Shot Power", "Long Shots", "Volleys", "Penalties"],
    "Passing": ["Vision", "Crossing", "Long Passing", "Short Passing", "Curve"],
    "Dribbling": ["Agility", "Balance", "Reactions", "Ball Control", "Dribbling"],
    "Defending": ["Interceptions", "Heading Accuracy", "Def Awareness", "Stand Tackle", "Slide Tackle"],
    "Physical": ["Jumping", "Stamina", "Strength", "Aggression"]
}

def get_category(stat_name):
    for cat, items in categories.items():
        # Αντιστοίχιση με fuzzy matching επειδή το CSV μπορεί να έχει "SprintSpeed" κολλητά
        if any(x in stat_name for x in items): return cat
    return "Other"

# --- VISUALIZATION ΤΩΝ SLIDERS ---
# Τα χωρίζουμε στις 3 στήλες
cols_iter = [col1, col2]
current_col_idx = 0

# Ταξινομούμε τα attributes ανά κατηγορία
sorted_attrs = sorted(attributes_list, key=lambda x: get_category(x['name']))
prev_cat = ""

with col1:
    st.subheader("Attributes")

for attr in sorted_attrs:
    cat = get_category(attr['name'])
    
    # Αλλαγή στήλης αν αλλάξει η κατηγορία (για ομορφιά)
    if cat != prev_cat:
        st.markdown(f"### {cat}")
        prev_cat = cat
    
    # Archetype Logic: Αν το Archetype δίνει μπονους, ανέβασε το Min
    bonus_min = arch_data["bonus"].get(attr['name'], 0)
    final_min = max(attr['base_min'], bonus_min)
    
    # Slider
    val = st.slider(
        f"{attr['name']}", 
        min_value=final_min, 
        max_value=99, 
        value=final_min,
        key=attr['name']
    )
    
    # Υπολογισμός Κόστους
    # Τύπος: (Current - Min) * Cost Factor
    cost_factor = 1
    if val > 85: cost_factor = 2
    if val > 92: cost_factor = 3
    
    cost = (val - final_min) * cost_factor
    user_costs += cost
    user_selections[attr['name']] = val

# --- 4. ΔΕΞΙΑ ΣΤΗΛΗ (PLAYSTYLES & RESULTS) ---
with col3:
    st.markdown("### 🛡️ Playstyles & Summary")
    
    # AP CARD
    remaining = total_ap - user_costs
    color = "#2ecc71" if remaining >= 0 else "#e74c3c"
    
    st.markdown(f"""
    <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center; color:white;">
        <h2>{remaining} AP Left</h2>
        <p>Used: {user_costs} / {total_ap}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.write("**Select Playstyles:**")
    for ps in FC_LOGIC["PLAYSTYLES"]:
        has_ps = st.checkbox(ps)
        if has_ps:
            # Dummy check - Εδώ θα μπει η λογική
            st.caption(f"Checking requirements for {ps}...")
            # Π.χ. Αν Finesse Shot -> Check Curve > 80
            if ps == "Finesse Shot" and user_selections.get("Curve", 0) < 80:
                st.error("⚠️ Need 80 Curve!")
            elif ps == "Rapid" and user_selections.get("Sprint Speed", 0) < 75:
                st.error("⚠️ Need 75 Sprint Speed!")
            else:
                st.success("✅ Active")
