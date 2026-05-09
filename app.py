import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Crime Data Analytics", layout="wide")

st.title("Crime Data Analytics Dashboard")

df = pd.read_excel("crime_data.xlsx")

st.subheader("Dataset Preview")
st.dataframe(df.head())

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Cases", len(df))

with col2:
    st.metric("Total Cities", df["City"].nunique())

with col3:
    st.metric("Crime Types", df["Crime Type"].nunique())

st.subheader("Crime Type Distribution")
fig = px.bar(df["Crime Type"].value_counts().reset_index(),
             x="Crime Type",
             y="count",
             title="Crime Type Count")
st.plotly_chart(fig, use_container_width=True)

st.subheader("City-wise Crime Count")
city_fig = px.bar(df["City"].value_counts().reset_index(),
                  x="City",
                  y="count",
                  title="City-wise Crime Cases")
st.plotly_chart(city_fig, use_container_width=True)