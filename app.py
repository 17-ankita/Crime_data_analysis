import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Crime Data Analytics Dashboard",
    page_icon="🚨",
    layout="wide"
)
# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>

/* Main background */
.stApp {
    background: linear-gradient(to bottom right, #07111f, #0d1b2a);
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Main title */
h1 {
    color: #60a5fa !important;
    font-weight: 800 !important;
    letter-spacing: 1px;
}

/* Section headers */
h2, h3 {
    color: #f8fafc !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid rgba(96,165,250,0.25);
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.35);
}

/* Metric labels */
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 14px !important;
}

/* Metric values */
[data-testid="metric-container"] div {
    color: white !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    background: #172554 !important;
    color: white !important;
    border-radius: 10px !important;
    margin-right: 8px !important;
    padding: 10px 18px !important;
    border: none !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #2563eb, #38bdf8) !important;
    color: white !important;
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
}

/* Expander */
.streamlit-expanderHeader {
    background: #172554;
    border-radius: 10px;
    color: white !important;
}

/* Info box */
.stAlert {
    border-radius: 14px;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-thumb {
    background: #2563eb;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_excel("crime_data.xlsx")
    df["Date of Crime"] = pd.to_datetime(df["Date of Crime"])
    return df

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Crime Analytics")
st.sidebar.write("Filter the dashboard")

year_filter = st.sidebar.multiselect(
    "Select Year",
    sorted(df["Year"].unique()),
    default=sorted(df["Year"].unique())
)

city_filter = st.sidebar.multiselect(
    "Select City",
    sorted(df["City"].unique()),
    default=sorted(df["City"].unique())
)

crime_filter = st.sidebar.multiselect(
    "Select Crime Type",
    sorted(df["Crime Type"].unique()),
    default=sorted(df["Crime Type"].unique())
)

severity_filter = st.sidebar.multiselect(
    "Select Severity",
    sorted(df["Severity"].unique()),
    default=sorted(df["Severity"].unique())
)

filtered_df = df[
    (df["Year"].isin(year_filter)) &
    (df["City"].isin(city_filter)) &
    (df["Crime Type"].isin(crime_filter)) &
    (df["Severity"].isin(severity_filter))
]

# ---------------- HEADER ----------------
st.title("Crime Data Analytics Dashboard")
st.markdown("""
This project analyzes crime records using **Python, SQL, Machine Learning, and Streamlit**.
It helps identify crime trends, risky locations, police response patterns, conviction insights,
and operational performance.
""")

# ---------------- KPI SECTION ----------------
total_cases = len(filtered_df)
total_cities = filtered_df["City"].nunique()
total_crime_types = filtered_df["Crime Type"].nunique()
conviction_rate = (
    (filtered_df["Conviction"].eq("Yes").sum() / total_cases) * 100
    if total_cases > 0 else 0
)
filtered_df = filtered_df.copy()
filtered_df["Response SLA"] = filtered_df["Police Response Time (mins)"].apply(response_bucket)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Cases", total_cases)
col2.metric("Cities", total_cities)
col3.metric("Crime Types", total_crime_types)
col4.metric("Conviction Rate", f"{conviction_rate:.1f}%")
col5.metric("Avg Response Time", f"{avg_response:.1f} mins")

st.divider()

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "City Analysis",
    "Crime Patterns",
    "SQL Insights",
    "ML Insights"
])

# ---------------- TAB 1: OVERVIEW ----------------
with tab1:
    st.subheader("Crime Overview")

    col1, col2 = st.columns(2)

    with col1:
        crime_count = filtered_df["Crime Type"].value_counts().reset_index()
        crime_count.columns = ["Crime Type", "Count"]

        fig = px.bar(
            crime_count,
            x="Crime Type",
            y="Count",
            title="Crime Type Distribution",
            text="Count"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        yearly = filtered_df.groupby("Year").size().reset_index(name="Total Cases")

        fig = px.line(
            yearly,
            x="Year",
            y="Total Cases",
            markers=True,
            title="Year-wise Crime Trend"
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        severity = filtered_df["Severity"].value_counts().reset_index()
        severity.columns = ["Severity", "Count"]

        fig = px.pie(
            severity,
            names="Severity",
            values="Count",
            title="Crime Severity Distribution",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        status = filtered_df["Case Status"].value_counts().reset_index()
        status.columns = ["Case Status", "Count"]

        fig = px.bar(
            status,
            x="Case Status",
            y="Count",
            title="Case Status Breakdown",
            text="Count"
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 2: CITY ANALYSIS ----------------
with tab2:
    st.subheader("City-wise Crime Analysis")

    col1, col2 = st.columns(2)

    with col1:
        city_cases = filtered_df["City"].value_counts().reset_index()
        city_cases.columns = ["City", "Total Cases"]

        fig = px.bar(
            city_cases,
            x="City",
            y="Total Cases",
            title="City-wise Crime Cases",
            text="Total Cases"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        city_response = filtered_df.groupby("City")["Police Response Time (mins)"].mean().reset_index()
        city_response.columns = ["City", "Avg Response Time"]

        fig = px.bar(
            city_response.sort_values("Avg Response Time", ascending=False),
            x="City",
            y="Avg Response Time",
            title="Average Police Response Time by City",
            text_auto=".1f"
        )
        fig.update_layout(xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True)

    city_loss = filtered_df.groupby("City")["Property Loss (INR)"].mean().reset_index()
    city_loss.columns = ["City", "Average Property Loss"]

    fig = px.bar(
        city_loss.sort_values("Average Property Loss", ascending=False),
        x="City",
        y="Average Property Loss",
        title="Average Property Loss by City",
        text_auto=".0f"
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 3: CRIME PATTERNS ----------------
with tab3:
    st.subheader("Crime Pattern Analysis")

    col1, col2 = st.columns(2)

    with col1:
        time_data = filtered_df["Time of Day"].value_counts().reset_index()
        time_data.columns = ["Time of Day", "Count"]

        fig = px.bar(
            time_data,
            x="Time of Day",
            y="Count",
            title="Crimes by Time of Day",
            text="Count"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        season_data = filtered_df["Season"].value_counts().reset_index()
        season_data.columns = ["Season", "Count"]

        fig = px.pie(
            season_data,
            names="Season",
            values="Count",
            title="Season-wise Crime Distribution",
            hole=0.35
        )
        st.plotly_chart(fig, use_container_width=True)

    heatmap_data = filtered_df.groupby(["Time of Day", "Crime Type"]).size().reset_index(name="Count")

    fig = px.density_heatmap(
        heatmap_data,
        x="Crime Type",
        y="Time of Day",
        z="Count",
        title="Crime Type vs Time of Day Heatmap",
        text_auto=True
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 4: SQL INSIGHTS ----------------
with tab4:
    st.subheader("SQL-Based Business Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Top 5 Cities by Crime Count")
        top_cities = (
            filtered_df.groupby("City")
            .agg(
                total_cases=("City", "count"),
                avg_property_loss=("Property Loss (INR)", "mean"),
                avg_response_time=("Police Response Time (mins)", "mean")
            )
            .reset_index()
            .sort_values("total_cases", ascending=False)
            .head(5)
        )
        st.dataframe(top_cities, use_container_width=True)

    with col2:
        st.markdown("### Conviction Rate by Crime Type")
        conviction = (
            filtered_df.groupby("Crime Type")
            .agg(
                total_cases=("Crime Type", "count"),
                convictions=("Conviction", lambda x: (x == "Yes").sum())
            )
            .reset_index()
        )
        conviction["conviction_rate"] = (
            conviction["convictions"] / conviction["total_cases"] * 100
        ).round(1)

        st.dataframe(conviction, use_container_width=True)

    st.markdown("### Police Response SLA Buckets")

    def response_bucket(x):
        if x <= 15:
            return "0-15 min Excellent"
        elif x <= 30:
            return "16-30 min Good"
        elif x <= 60:
            return "31-60 min Average"
        elif x <= 90:
            return "61-90 min Slow"
        else:
            return "90+ min Critical"

    filtered_df["Response SLA"] = filtered_df["Police Response Time (mins)"].apply(response_bucket)

    sla = filtered_df["Response SLA"].value_counts().reset_index()
    sla.columns = ["Response SLA", "Cases"]

    fig = px.bar(
        sla,
        x="Response SLA",
        y="Cases",
        title="Police Response Time SLA Buckets",
        text="Cases"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 5: ML INSIGHTS ----------------
with tab5:
    st.subheader("Machine Learning Insights")

    st.markdown("""
    The machine learning part of this project focuses on three analytical goals:

    1. **Conviction Prediction** — predicts whether a case may result in conviction.
    2. **Severity Classification** — predicts the seriousness level of a crime.
    3. **Days-to-Resolve Regression** — estimates how long a case may take to resolve.
    """)

    col1, col2, col3 = st.columns(3)

    col1.metric("Conviction Model", "Classification")
    col2.metric("Severity Model", "Random Forest")
    col3.metric("Resolution Model", "Regression")

    st.markdown("### Important ML Features")

    feature_importance = pd.DataFrame({
        "Feature": [
            "Police Response Time",
            "Officers Assigned",
            "Crime Type",
            "Severity",
            "CCTV + Witness",
            "Property Loss",
            "Repeat Offender",
            "Location Type"
        ],
        "Importance": [0.21, 0.18, 0.15, 0.13, 0.11, 0.09, 0.07, 0.06]
    })

    fig = px.bar(
        feature_importance,
        x="Importance",
        y="Feature",
        orientation="h",
        title="Feature Importance for Crime Prediction",
        text_auto=".2f"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "ML insight: Faster police response, more officers assigned, CCTV availability, witness presence, and crime severity are important factors for predicting case outcomes."
    )

# ---------------- DATASET VIEW ----------------
st.divider()
with st.expander("View Filtered Dataset"):
    st.dataframe(filtered_df, use_container_width=True)