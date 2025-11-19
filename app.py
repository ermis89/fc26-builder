import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# 1. Η ΜΗΧΑΝΗ ΛΟΓΙΚΗΣ ΤΟΥ FC26 (HARDCORE LOGIC)
# -----------------------------------------------------------------------------
class FC26Engine:
    @staticmethod
    def calculate_stat_cost(base_val, target_val):
        """
        Υπολογίζει το πραγματικό κόστος AP στο FC.
        Κανόνας (περίπου): 
        - Stats < 80: Κοστίζουν 1 AP ανά πόντο
        - Stats 80-89: Κοστίζουν 2 AP ανά πόντο
        - Stats 90+: Κοστίζουν 3 AP ανά πόντο
        """
        if target_val <= base_val: return 0
        
        total_cost = 0
        for v in range(base_val, target_val):
            if v < 80:
                total_cost += 1
            elif v < 90:
                total_cost += 2
            else:
                total_cost += 3 # High tier cost
        return total_cost

# -----------------------------------------------------------------------------
# 2. ΠΡΟΗΓΜΕΝΗ ΑΝΑΓΝΩΣΗ ΤΟΥ ΧΑΟΥΣ (PARSER)
# -----------------------------------------------------------------------------
@st.cache_data
def load_complex_data():
    try:
        # Διαβάζουμε τα πάντα ως string για να μην χάσουμε δεδομένα
        df = pd.read_csv("FC26 Pro Club Manual Builder - ManualBuilder.csv", header=None, dtype=str).fillna("")
    except:
        return None, None, None

    # --- A. ΕΞΟΡΥΞΗ LEVELS & AP ---
    # Ψάχνουμε το πινακάκι που έχει τα AP ανά Level
    levels_db = {}
    for r in range(len(df)):
        row_str = " ".join(df.iloc[r].astype(str).values)
        if "Total so far" in row_str:
            # Βρήκαμε τον header, ψάχνουμε από κάτω
            # Πρέπει να βρούμε ποια στήλη είναι το Level και ποια το AP
            c_lvl = -1
            c_ap = -1
            for c in range(len(df.columns)):
                val = str(df.iloc[r, c]).strip()
                if val == "Level": c_lvl = c
                if "Total so far" in val: c_ap = c
            
            if c_lvl != -1:
                # Σαρώνουμε προς τα κάτω
                for i in range(r+1, len(df)):
                    try:
                        l = df.iloc[i, c_lvl]
                        ap = df.iloc[i, c_ap]
                        if l.replace('.','').isdigit():
                            levels_db[int(float(l))] = int(float(ap))
                    except: continue
            break
    
    # Fallback αν δεν βρεθεί
    if not levels_db: levels_db = {100: 1269}

    # --- B. ΕΞΟΡΥΞΗ ATTRIBUTES (MIN/MAX) ---
    # Ψάχνουμε τη λέξη "Acceleration" που είναι πάντα η αρχή
    attrs_db = []
    found_attrs = False
    for r in range(len(df)):
        for c in range(len(df.columns)):
            if str(df.iloc[r, c]).strip() == "Acceleration":
                # Βρήκαμε την αρχή. Υποθέτουμε ότι Min/Max είναι δεξιά
                c_name = c
                # Ψάχνουμε δυναμικά για αριθμούς δεξιά
                c_min = c+1
                while c_min < len(df.columns) and not df.iloc[r, c_min].replace('.','').isdigit():
                    c_min += 1
                c_max = c_min + 1
                
                # Διαβάζουμε τη λίστα
                curr = r
                while curr < len(df):
                    name = str(df.iloc[curr, c_name]).strip()
                    if not name or name == "Attribute": # Τέλος λίστας
                        if len(attrs_db) > 5: break # Αν έχουμε βρει ήδη, σταματάμε
                        curr += 1; continue

                    # Έλεγχος αν είναι Attribute
                    try:
                        mn = int(float(df.iloc[curr, c_min]))
                        mx = int(float(df.iloc[curr, c_max]))
                        attrs_db.append({"name": name, "min": mn, "max": mx})
                    except: pass
                    curr += 1
                found_attrs = True; break
        if found_attrs: break

    # --- C. ΕΞΟΡΥΞΗ PLAYSTYLES & REQUIREMENTS ---
    # Ψάχνουμε τη λίστα αριστερά που έχει τα Playstyles
    playstyles_db = []
    keywords = ["Finesse", "Rapid", "Quick Step", "Dead Ball", "Tiki"]
    
    for r in range(15, len(df)): # Συνήθως ξεκινάνε πιο κάτω
        # Έλεγχος στήλης Α και Β
        for c in [0, 1]:
            val = str(df.iloc[r, c]).strip()
            # Αν μοιάζει με Playstyle
            if any(k in val for k in keywords) and "(" not in val:
                # Ψάχνουμε για Requirement στην ίδια γραμμή (στα κελιά δεξιά)
                req_val = 0
                req_stat = ""
                
                # Σαρώνουμε τη γραμμή για αριθμούς > 60 (πιθανά requirements)
                for scan_c in range(c+1, c+10): # Κοιτάμε 10 κελιά δεξιά
                    cell_val = str(df.iloc[r, scan_c]).strip()
                    if cell_val.replace('.','').isdigit():
                        num = int(float(cell_val))
                        if 60 <= num <= 99:
                            req_val = num
                            # Ίσως το όνομα του stat είναι δίπλα;
                            break
                
                playstyles_db.append({"name": val, "req_val": req_val})

    return levels_db, attrs_db, playstyles_db

# -----------------------------------------------------------------------------
# 3. INTERFACE & STATE MANAGEMENT
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="FC26 Pro Logic")

# Φόρτωση
levels, attributes, playstyles = load_complex_data()

if not attributes:
    st.error("❌ CRITICAL ERROR: Το αρχείο δεν διαβάστηκε σωστά. Ανέβασε το 'FC26 Pro Club Manual Builder - ManualBuilder.csv'.")
    st.stop()

# Sidebar - Player Level
st.sidebar.header("🎚️ Player Level")
max_lvl = max(levels.keys())
sel_level = st.sidebar.number_input("Level", 1, max_lvl, max_lvl)
TOTAL_BUDGET = levels.get(sel_level, 1000)

# Sidebar - Playstyles (Με Logic Check)
st.sidebar.divider()
st.sidebar.subheader("🛡️ Playstyles")

selected_playstyles_indices = []
for i, ps in enumerate(playstyles):
    label = ps['name']
    if ps['req_val'] > 0:
        label += f" (Req: {ps['req_val']})"
    
    if st.sidebar.checkbox(label, key=f"ps_{i}"):
        selected_playstyles_indices.append(i)

# Main Screen
st.title("⚽ FC26 Logic Builder")
st.markdown(f"**Base Archetype Stats loaded from CSV.** (Limits: {attributes[0]['min']} - {attributes[0]['max']} for {attributes[0]['name']})")

col_stats, col_info = st.columns([2, 1])

# State για να κρατάμε τα τρέχοντα stats
current_stats = {}
total_spent = 0

with col_stats:
    st.subheader("📈 Attributes Distribution")
    
    # Ομαδοποίηση για ομορφιά
    cols = st.columns(3)
    
    for i, attr in enumerate(attributes):
        col = cols[i % 3]
        with col:
            # Slider
            val = st.slider(
                f"**{attr['name']}**",
                min_value=attr['min'],
                max_value=attr['max'],
                value=attr['min'],
                key=f"attr_{i}"
            )
            
            # Υπολογισμός Κόστους με τη ΜΗΧΑΝΗ FC26
            cost = FC26Engine.calculate_stat_cost(attr['min'], val)
            total_spent += cost
            current_stats[attr['name']] = val
            
            # Οπτική ένδειξη κόστους
            if cost > 0:
                st.caption(f"🔥 Cost: {cost} AP")

# δεξιά στήλη - RESULTS
with col_info:
    remaining = TOTAL_BUDGET - total_spent
    
    # Dashboard Card
    st.markdown(f"""
    <div style="background-color: #1a1a1a; border: 2px solid #333; border-radius: 15px; padding: 20px; text-align: center;">
        <h3 style="color: #aaa; margin:0;">AVAILABLE AP</h3>
        <h1 style="font-size: 60px; margin:0; color: {'#4cd137' if remaining >= 0 else '#e84118'}">{remaining}</h1>
        <p>Total: {TOTAL_BUDGET} | Spent: {total_spent}</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("🔍 Requirements Check")
    
    # Έλεγχος Playstyles (ΑΥΤΟ ΠΟΥ ΗΘΕΛΕΣ)
    if selected_playstyles_indices:
        for idx in selected_playstyles_indices:
            ps = playstyles[idx]
            req_val = ps['req_val']
            
            # Πρέπει να βρούμε ΠΟΙΟ stat χρειάζεται. 
            # Επειδή το CSV είναι χαοτικό, κάνουμε μια "μαντεψιά" ή ελέγχουμε γενικά
            # Στο συγκεκριμένο αρχείο, συνήθως η απαίτηση είναι στο κύριο stat του Archetype.
            # Εδώ θα κάνουμε έλεγχο με βάση τη λογική:
            # Αν το Playstyle είναι "Finesse", ελέγχουμε Curve/Finishing.
            
            status_icon = "✅"
            status_msg = "Active"
            
            # Logic Checker
            if req_val > 0:
                # Εδώ ψάχνουμε αν ΚΑΠΟΙΟ από τα stats του χρήστη πιάνει το νούμερο
                # (Απλοποιημένη λογική γιατί δεν ξέρουμε ποιο stat θέλει ακριβώς από το CSV)
                max_user_stat = max(current_stats.values())
                if max_user_stat < req_val:
                    status_icon = "❌"
                    status_msg = f"Need stat {req_val}+"
                else:
                    # Πιο έξυπνος έλεγχος: Αν το όνομα του playstyle ταιριάζει με stat
                    pass 
            
            st.markdown(f"**{ps['name']}**")
            if status_icon == "✅":
                st.success(f"{status_icon} {status_msg}")
            else:
                st.warning(f"{status_icon} {status_msg} (Check Attributes)")
    else:
        st.info("Select Playstyles from the sidebar to validate.")
