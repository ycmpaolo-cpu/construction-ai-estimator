import pandas as pd
import streamlit as st
import requests
from pricing_engine import MaterialIntelligence

# Load logical parts list
tasks = pd.read_csv("tasks.csv")
assemblies = pd.read_csv("assemblies.csv")
pricing_engine = MaterialIntelligence()

st.title("AI Construction Estimator")
st.markdown("Powered by **Material Intelligence Pricing Engine** & **DDC-CWICR API**")

scope = st.text_input("Enter Construction Scope (e.g., 'install architectural shingles with ice guard')")
sq = st.number_input("Quantity (Roof Squares)", value=20.0, min_value=1.0)

if scope:
    st.header("1. Task Detection & Material List")
    
    # We use our tasks library to identify the components required
    matched = tasks[tasks['keywords'].str.contains(scope, case=False, na=False)]
    
    if not matched.empty:
        st.write(f"Detected Tasks from Core Assemblies: **{', '.join(matched['task'].tolist())}**")
        st.write("---")
        
        st.header("2. Live Supplier Pricing")
        
        total_estimate = 0
        
        for assembly in matched["assembly"]:
            parts = assemblies[assemblies["assembly"] == assembly]
            
            for _, row in parts.iterrows():
                generic_material = row["material"]
                unit = row["unit"]
                qty = float(row["quantity"]) * sq
                
                # Material Intelligence Live Lookup!
                best_price, best_supplier, best_brand, all_options = pricing_engine.get_best_price(generic_material)
                
                if best_price != float('inf'):
                    cost = qty * best_price
                    total_estimate += cost
                    
                    st.markdown(f"**{generic_material}** ({qty:g} {unit})")
                    st.success(f"Best Price: **{best_supplier}** ({best_brand}) - **${best_price:.2f}/{unit}**")
                    
                    comparison_str = " | ".join([f"{o['supplier']}: ${o['price']:.2f}" for o in all_options])
                    st.caption(f"*Supplier comparison: {comparison_str}*")
                    st.write(f"-> **Subtotal:** ${cost:,.2f}")
                    st.write("")
                else:
                    st.warning(f"Pricing not found for {generic_material} anywhere.")
                    
        st.divider()
        st.subheader(f"Total Local Estimate: ${total_estimate:,.2f}")
        
    st.write("---")
    st.header("3. Extra DDC-CWICR Knowledge Library Tasks")
    st.caption("Searching the global 55,000+ items database for broader scope definitions...")
    try:
        response = requests.get(
            "https://buildcalculator.io/api/v1/search",
            params={"q": scope, "lang": "en", "top": 3}
        )
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            for item in data["results"]:
                name = item.get("name", "Unknown")
                unit_price = item.get("pricing", {}).get("total_per_unit", 0)
                st.write(f"- **{name}**: ${unit_price:,.2f} per {item.get('unit', 'unit')}")
    except Exception:
        pass

