import pandas as pd
import streamlit as st
import requests

# We still load the local CSVs as fallback or for user-specific custom rates if needed, 
# but for the main estimator, we will rely on the 10,000+ items DDC-CWICR Knowledge Library API.
# tasks = pd.read_csv("tasks.csv")
# assemblies = pd.read_csv("assemblies.csv")
# prices = pd.read_csv("prices.csv")

st.title("AI Construction Estimator")
st.markdown("Powered by the **DDC-CWICR 55,000+ Task Knowledge Library**")

scope = st.text_input("Enter Construction Scope (e.g., 'install architectural shingles with ice guard')")

qty_input = st.number_input("Quantity", value=1.0, min_value=0.1)

if scope:
    st.subheader("Searching Knowledge Library...")
    
    # Query the BuildCalculator.io API
    try:
        response = requests.get(
            "https://buildcalculator.io/api/v1/search",
            params={"q": scope, "lang": "en", "top": 5}
        )
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            st.success(f"Found {len(data['results'])} matching assemblies!")
            
            total_estimate = 0
            
            for item in data["results"]:
                name = item.get("name", "Unknown Task")
                unit = item.get("unit", "units")
                pricing = item.get("pricing", {})
                
                # API returns pricing per unit. We multiply by the user's quantity.
                unit_price = pricing.get("total_per_unit", 0)
                labor = pricing.get("labor_per_unit", 0)
                material = pricing.get("material_per_unit", 0)
                equipment = pricing.get("equipment_per_unit", 0)
                
                # Calculate costs based on user quantity
                task_total = unit_price * qty_input
                total_estimate += task_total
                
                with st.expander(f"{name} ({unit_price} / {unit})"):
                    st.write(f"**Calculated Cost for {qty_input} {unit}(s):** ${task_total:,.2f}")
                    st.markdown(f"""
                    - **Labor:** ${labor * qty_input:,.2f}
                    - **Material:** ${material * qty_input:,.2f}
                    - **Equipment:** ${equipment * qty_input:,.2f}
                    """)
                    
            st.divider()
            st.subheader(f"Total Estimated Cost: ${total_estimate:,.2f}")
            
        else:
            st.warning("No matching tasks found in the database. Try rephrasing your scope.")
            
    except Exception as e:
        st.error(f"Failed to connect to the Knowledge Library: {e}")

