import pandas as pd
import streamlit as st

tasks = pd.read_csv("tasks.csv")
assemblies = pd.read_csv("assemblies.csv")
prices = pd.read_csv("prices.csv")

scope = st.text_input("Enter Scope")

sq = st.number_input("Roof Squares", value=20)

if scope:

    matched = tasks[tasks['keywords'].str.contains(scope, case=False, na=False)]

    st.subheader("Detected Tasks")
    st.write(matched["task"])

    total = 0

    for assembly in matched["assembly"]:

        parts = assemblies[assemblies["assembly"] == assembly]

        for _, row in parts.iterrows():

            material = row["material"]
            qty = row["quantity"] * sq

            price_row = prices[prices["material"] == material]

            if not price_row.empty:
                price = price_row.iloc[0]["price"]

                cost = qty * price
                total += cost

                st.write(material, qty, "$", cost)

    st.subheader("Total Material Cost")
    st.write("$", total)
