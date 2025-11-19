import streamlit as st
import pandas as pd

# --- 1. Η ΛΟΓΙΚΗ ΤΟΥ FC26 (Database) ---
# Εδώ θα βάλουμε τους κανόνες που χάθηκαν από το Excel
# Επειδή δεν μπορώ να δω τα formulas σου, βάζω τα δεδομένα όπως τα ξέρουμε από το community

FC26_DATA = {
    "ARCHETYPES": {
        "Magician": {
            "base_stats": {"Agility": 85, "Dribbling": 84, "Vision": 82},
            "limits": {"Agility": 95, "Dribbling": 96}, # Max Caps
            "cost_modifier": 1.0
        },
        "Finisher": {
            "base_stats": {"Finishing": 86, "Shot Power": 80},
            "limits": {"Finishing": 99, "Shot Power": 95},
            "cost_modifier": 1.0
        },
        "Marauder": {
            "base_stats": {"Sprint Speed": 78, "Acceleration": 79},
            "limits": {"Sprint Speed": 92, "Acceleration": 94},
            "cost_modifier": 1.1 # Π.χ. κοστίζει πιο ακριβά
        }
    },
    "PLAYSTYLES": {
        "Finesse Shot+": {"Curve": 85, "Finishing": 80},
        "Rapid+": {"Sprint Speed": 85, "Acceleration": 80},
        "Quick Step+": {"Acceleration": 85},
        "Dead Ball+": {"Curve": 85, "Shot Power": 80}
    }
}

def calculate_ap_for_level(level):
    """Υπολογίζει τα AP βάσει του Level (FC26 Logic)"""
    # Αυτά είναι τα επίσημα νούμερα (περίπου)
    if level <= 10: return 100 + (level * 2)
    if level <= 50: return 120 + (level * 3)
    return 160 # Max AP (π.χ.)

# --- 2. ΤΟ UI ΤΗΣ ΕΦΑΡΜΟΓΗΣ ---
st.set_page_config(layout="wide", page_title="FC26 Builder")

st.title("⚽ FC26 Pro Clubs Builder")

# Sidebar: Setup
with st.sidebar:
    st.header("Player Setup")
    selected_arch = st.selectbox("Archetype", list(FC26_DATA["ARCHETYPES"].keys()))
    level = st.slider("Level", 1, 100, 100)
    
    # Υπολογισμός AP
    total_ap = calculate_ap_for_level(level)
    st.metric("Διαθέσιμα AP", total_ap)

# Main Area: Attributes
st.subheader(f"Build: {selected_arch}")

col1, col2, col3 = st.columns(3)

# Παίρνουμε τα όρια του Archetype
arch_limits = FC26_DATA["ARCHETYPES"][selected_arch]["limits"]
arch_base = FC26_DATA["ARCHETYPES"][selected_arch]["base_stats"]

# Dict για να κρατάμε τα user stats
user_stats = {}

with col1:
    st.markdown("### Pace & Dribbling")
    # Παράδειγμα Loop για sliders
    for stat in ["Acceleration", "Sprint Speed", "Agility", "Balance", "Dribbling"]:
        # Default limits αν δεν υπάρχουν στο Archetype
        min_val = arch_base.get(stat, 60)
        max_val = arch_limits.get(stat, 99)
        
        user_stats[stat] = st.slider(stat, min_val, 99, min_val)

with col2:
    st.markdown("### Shooting & Passing")
    for stat in ["Finishing", "Shot Power", "Long Shots", "Vision", "Curve"]:
        min_val = arch_base.get(stat, 60)
        user_stats[stat] = st.slider(stat, min_val, 99, min_val)

# --- 3. Η ΛΟΓΙΚΗ ΕΛΕΓΧΟΥ (VALIDATION) ---
# Εδώ ελέγχουμε αν το build είναι νόμιμο

with col3:
    st.markdown("### Validation & Playstyles")
    
    used_ap = 0
    # Απλή λογική κόστους (Πρέπει να την κάνουμε πιο σύνθετη όπως το Excel σου)
    for stat, val in user_stats.items():
        base = 60 # Υπόθεση
        diff = val - base
        if diff > 0:
            used_ap += diff # Κάθε πόντος κοστίζει 1 AP (Θα το αλλάξουμε)

    remaining = total_ap - used_ap
    
    if remaining >= 0:
        st.success(f"✅ AP OK: {remaining} left")
    else:
        st.error(f"⛔ Over Budget: {remaining}")

    st.divider()
    st.markdown("**Playstyle Check:**")
    
    # Έλεγχος για Finesse Shot+
    reqs = FC26_DATA["PLAYSTYLES"]["Finesse Shot+"]
    has_requirements = True
    for r_stat, r_val in reqs.items():
        if user_stats.get(r_stat, 0) < r_val:
            has_requirements = False
            st.warning(f"❌ **Finesse Shot+**: Θέλει {r_stat} {r_val}")
    
    if has_requirements:
        st.success("✅ Unlocked: Finesse Shot+")
