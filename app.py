import pandas as pd
import streamlit as st
import requests
import cv2
from pricing_engine import MaterialIntelligence
from blueprint_engine import BlueprintEngine

# Initialization
tasks = pd.read_csv("tasks.csv")
assemblies = pd.read_csv("assemblies.csv")
pricing_engine = MaterialIntelligence()
blueprint_engine = BlueprintEngine()

st.set_page_config(page_title="AI Estimator", layout="wide")

st.title("🏗️ AI Construction Estimator Pro")
st.markdown("Powered by **Material Intelligence Pricing**, **Computer Vision OCR**, & **DDC-CWICR DB**")

tab1, tab2 = st.tabs(["📝 Text Scope Estimator", "📐 Blueprint Parser"])

# --- TAB 1: Text Scope ---
with tab1:
    scope = st.text_input("Enter Construction Scope (e.g., 'install architectural shingles with ice guard')")
    sq = st.number_input("Quantity (Roof Squares)", value=20.0, min_value=1.0)
    
    if scope:
        st.header("1. Task Detection & Material List")
        matched = tasks[tasks['keywords'].str.contains(scope, case=False, na=False)]
        
        if not matched.empty:
            st.write(f"Detected Tasks from Core Assemblies: **{', '.join(matched['task'].tolist())}**")
            st.divider()
            
            st.header("2. Live Supplier Pricing")
            total_estimate = 0
            
            for assembly in matched["assembly"]:
                parts = assemblies[assemblies["assembly"] == assembly]
                for _, row in parts.iterrows():
                    generic_material = row["material"]
                    unit = row["unit"]
                    qty = float(row["quantity"]) * sq
                    
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
                        st.warning(f"Pricing not found for {generic_material}.")
            
            st.divider()
            st.subheader(f"Total Local Estimate: ${total_estimate:,.2f}")
            
        st.write("---")
        st.header("3. Extra DDC-CWICR Knowledge Library Tasks")
        try:
            response = requests.get(
                "https://buildcalculator.io/api/v1/search",
                params={"q": scope, "lang": "en", "top": 3}
            )
            
            if response.status_code == 403:
                st.warning("⚠️ **API Limit Reached:** The BuildCalculator API has temporarily blocked requests from this server due to fair-use limits. (This is common on free shared hosting like Streamlit Cloud).")
            else:
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    for item in data["results"]:
                        name = item.get("name", "Unknown")
                        unit_price = item.get("pricing", {}).get("total_per_unit", 0)
                        st.write(f"- **{name}**: ${unit_price:,.2f} per {item.get('unit', 'unit')}")
        except Exception as e:
            st.error(f"Could not connect to Knowledge Library: {e}")

# --- TAB 2: Blueprint Engine ---
with tab2:
    st.markdown("### Upload your construction blueprint to automatically extract dimensions and calculate materials.")
    blueprint_file = st.file_uploader("Upload Blueprint (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])
    
    if blueprint_file:
        with st.spinner("Parsing blueprint with Computer Vision and OCR..."):
            
            images = []
            if blueprint_file.name.lower().endswith('.pdf'):
                st.info("Converting PDF pages to images...")
                images = blueprint_engine.pdf_to_image(blueprint_file)
            else:
                images = blueprint_engine.process_image(blueprint_file)
                
            if images:
                # Preview the first parsed image
                st.image(cv2.cvtColor(images[0], cv2.COLOR_BGR2RGB), caption="Blueprint Preview", use_column_width=True)
                
                st.header("1. OCR Dimension Extraction")
                components = blueprint_engine.extract_dimensions(images[0])
                
                # If OCR didn't find specific mock formatting, use a dummy one for demonstration purposes
                if not components:
                    st.warning("OCR could not read strictly formatted dimensions ('Roof 24'x36''). Injecting dummy detected roof for demonstration.")
                    components = [{"component": "roof", "width": 40, "length": 50}]
                
                st.json(components)
                
                st.header("2. Automated Material Calculations")
                materials = blueprint_engine.calculate_materials(components, assemblies)
                st.dataframe(pd.DataFrame(materials))
                
                st.header("3. Live Supplier Integration")
                total_cost = 0
                
                for item in materials:
                    supplier, price = pricing_engine.get_best_price(item["material"])[:2]
                    
                    if price != float('inf'):
                        cost = price * item["quantity"]
                        total_cost += cost
                        st.success(f"**{item['material']}** ({item['quantity']} {item['unit']}) - {supplier} **${price:.2f}/{item['unit']}**")
                        st.write(f"-> **Calculated Subtotal:** ${cost:,.2f}")
                    else:
                        st.warning(f"Missing pricing for {item['material']}.")
                        
                st.divider()
                st.subheader(f"Total Blueprint Estimate: ${total_cost:,.2f}")

