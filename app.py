import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import re

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Agri Mandi-to-Market Supply Chain Optimizer",
    page_icon="🌾",
    layout="wide"
)

# ============================================================
# ROOT PATH
# ============================================================

BASE = Path(__file__).resolve().parent

ARRIVALS_FILE = BASE / "arrivals_fact.csv"
PRICES_FILE = BASE / "prices_fact.csv"
MANDI_FILE = BASE / "mandi_dim.csv"
TRANSPORT_FILE = BASE / "transport_fact.csv"
WEATHER_FILE = BASE / "weather_daily.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.replace("Rs", "", regex=False)
        .str.replace("INR", "", regex=False)
        .str.replace(r"[^0-9.\-]", "", regex=True),
        errors="coerce"
    )


# ============================================================
# CROP NAME STANDARDIZATION
# ============================================================

CROP_MAP = {
    "basmati": "Rice", "chawal": "Rice", "rice": "Rice",
    "paddy": "Rice", "dhan": "Rice", "dhaan": "Rice",
    "धान": "Rice", "चावल": "Rice",
    "corn": "Maize", "maize": "Maize", "makka": "Maize",
    "makki": "Maize", "मक्का": "Maize",
    "cotton": "Cotton", "kapas": "Cotton", "narma": "Cotton",
    "कपास": "Cotton",
    "wheat": "Wheat", "gehun": "Wheat", "gehu": "Wheat",
    "kanak": "Wheat", "गेहूं": "Wheat",
    "mustard": "Mustard", "sarso": "Mustard", "sarson": "Mustard",
    "सरसों": "Mustard",
    "sugarcane": "Sugarcane", "ganna": "Sugarcane",
    "ganne": "Sugarcane", "गन्ना": "Sugarcane"
}


VALID_CROPS = [
    "Cotton",
    "Maize",
    "Mustard",
    "Rice",
    "Sugarcane",
    "Wheat"
]

def normalize_crop_value(x):
    if pd.isna(x):
        return np.nan
    return CROP_MAP.get(str(x).strip().lower(), np.nan)


def normalize_mandi_value(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().upper()
    match = re.search(r"(\d+)", s)
    if match:
        return f"MANDI{int(match.group(1)):03d}"
    return s


def find_column(df, candidates):
    """Find the first available column from a list."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def parse_dates(df, candidates):
    col = find_column(df, candidates)

    if col is None:
        return None

    df[col] = pd.to_datetime(
        df[col],
        errors="coerce",
        dayfirst=True
    )

    return col


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    arrivals = pd.read_csv(ARRIVALS_FILE)
    prices = pd.read_csv(PRICES_FILE)
    mandi = pd.read_csv(MANDI_FILE)

    # Standardize mandi IDs consistently across datasets.
    for df in [arrivals, prices, mandi]:
        if "mandi_id" in df.columns:
            df["mandi_id"] = df["mandi_id"].apply(normalize_mandi_value)

    try:
        transport = pd.read_csv(TRANSPORT_FILE)
    except Exception:
        transport = pd.DataFrame()

    try:
        weather = pd.read_csv(WEATHER_FILE)
    except Exception:
        weather = pd.DataFrame()

    # -----------------------------
    # ARRIVALS
    # -----------------------------

    arrival_date_col = parse_dates(
        arrivals,
        ["date", "arrival_date", "arrival_time"]
    )

    if arrival_date_col:
        arrivals["_date"] = arrivals[arrival_date_col].dt.date

    crop_col_a = find_column(
        arrivals,
        ["crop_name", "crop", "commodity"]
    )

    quantity_col = find_column(
        arrivals,
        [
            "arrival_quantity_qtl",
            "quantity_qtl",
            "arrival_quantity",
            "quantity"
        ]
    )

    if quantity_col:
        arrivals["_quantity"] = clean_number(arrivals[quantity_col])
    else:
        arrivals["_quantity"] = np.nan

    if crop_col_a:
        arrivals["_crop"] = arrivals[crop_col_a].apply(normalize_crop_value)
        arrivals[crop_col_a] = arrivals["_crop"]

    # -----------------------------
    # PRICES
    # -----------------------------

    price_date_col = parse_dates(
        prices,
        ["date", "price_date", "arrival_date"]
    )

    if price_date_col:
        prices["_date"] = prices[price_date_col].dt.date

    crop_col_p = find_column(
        prices,
        ["crop_name", "crop", "commodity"]
    )

    modal_col = find_column(
        prices,
        ["modal_price", "modal", "market_price", "price"]
    )

    msp_col = find_column(
        prices,
        ["msp", "MSP"]
    )

    if crop_col_p:
        prices["_crop"] = prices[crop_col_p].apply(normalize_crop_value)
        prices[crop_col_p] = prices["_crop"]

    if modal_col:
        prices["_modal_price"] = clean_number(prices[modal_col])
    else:
        prices["_modal_price"] = np.nan

    if msp_col:
        prices["_msp"] = clean_number(prices[msp_col])
    else:
        prices["_msp"] = np.nan

    # -----------------------------
    # TRANSPORT
    # -----------------------------

    if not transport.empty:

        transit_col = find_column(
            transport,
            ["transit_hours", "transit_time", "travel_hours"]
        )

        distance_col = find_column(
            transport,
            ["distance_km", "distance", "distance_miles"]
        )

        if transit_col:
            transport["_transit_hours"] = clean_number(
                transport[transit_col]
            )
        else:
            transport["_transit_hours"] = np.nan

        if distance_col:
            transport["_distance"] = clean_number(
                transport[distance_col]
            )
        else:
            transport["_distance"] = np.nan

    return arrivals, prices, mandi, transport, weather


# ============================================================
# LOAD AGENT DATA
# ============================================================

@st.cache_data
def load_agent_data():

    # IMPORTANT:
    # All files are in the GitHub ROOT folder.

    arrivals_agent = pd.read_csv(BASE / "arrivals_fact.csv")
    prices_agent = pd.read_csv(BASE / "prices_fact.csv")

    # Optional files
    try:
        mandi_agent = pd.read_csv(BASE / "mandi_dim.csv")
    except Exception:
        mandi_agent = pd.DataFrame()

    # Date parsing
    for df in [arrivals_agent, prices_agent]:

        date_candidates = [
            "date",
            "arrival_date",
            "price_date",
            "arrival_time"
        ]

        for col in date_candidates:

            if col in df.columns:

                df[col] = pd.to_datetime(
                    df[col],
                    errors="coerce",
                    dayfirst=True
                )

                if df[col].notna().sum() > 0:
                    df["_agent_date"] = df[col].dt.date
                    break

    # Crop normalization
    for df in [arrivals_agent, prices_agent]:

        crop_col = find_column(
            df,
            ["crop_name", "crop", "commodity"]
        )

        if crop_col:
            df["_agent_crop"] = (
                df[crop_col]
                .astype(str)
                .str.strip()
                .str.lower()
            )

    # Quantity
    quantity_col = find_column(
        arrivals_agent,
        [
            "arrival_quantity_qtl",
            "quantity_qtl",
            "arrival_quantity",
            "quantity"
        ]
    )

    if quantity_col:

        arrivals_agent["_agent_quantity"] = clean_number(
            arrivals_agent[quantity_col]
        )

    else:

        arrivals_agent["_agent_quantity"] = np.nan

    # Price
    modal_col = find_column(
        prices_agent,
        [
            "modal_price",
            "modal",
            "market_price",
            "price"
        ]
    )

    if modal_col:

        prices_agent["_agent_modal_price"] = clean_number(
            prices_agent[modal_col]
        )

    else:

        prices_agent["_agent_modal_price"] = np.nan

    # MSP
    msp_col = find_column(
        prices_agent,
        ["msp", "MSP"]
    )

    if msp_col:

        prices_agent["_agent_msp"] = clean_number(
            prices_agent[msp_col]
        )

    else:

        prices_agent["_agent_msp"] = np.nan

    return arrivals_agent, prices_agent, mandi_agent


# ============================================================
# LOAD EVERYTHING
# ============================================================

try:

    arrivals, prices, mandi, transport, weather = load_data()

except Exception as e:

    st.error("Unable to load dashboard data.")
    st.exception(e)
    st.stop()


# ============================================================
# TITLE
# ============================================================

st.title("🌾 Agri Mandi-to-Market Supply Chain Optimizer")

st.markdown(
    """
    **Track 3 – AgriTech**

    Transforming messy mandi data into clean, validated and actionable
    supply-chain insights.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🎛️ Dashboard Controls")


# Crop filter
crop_col = find_column(
    arrivals,
    ["_crop", "crop_name", "crop", "commodity"]
)

if crop_col:
    crop_values = [
        c for c in VALID_CROPS
        if c in arrivals[crop_col].dropna().astype(str).unique()
    ]

    selected_crop = st.sidebar.selectbox(
        "🌾 Crop",
        ["All"] + crop_values
    )
else:
    selected_crop = "All"


# Mandi filter
mandi_col = find_column(
    arrivals,
    ["mandi_name", "mandi", "mandi_id"]
)

if mandi_col:
    mandi_values = sorted(
        arrivals[mandi_col]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_mandi = st.sidebar.selectbox(
        "🏪 Mandi",
        ["All"] + mandi_values
    )
else:
    selected_mandi = "All"


# Time period filter
st.sidebar.subheader("📅 Time Period")

if "_date" in arrivals.columns:
    arrival_dates = pd.to_datetime(arrivals["_date"], errors="coerce")
    min_date = arrival_dates.min()
    max_date = arrival_dates.max()

    time_period = st.sidebar.selectbox(
        "Select Time Period",
        ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"]
    )

    if time_period == "Last 7 Days":
        period_start = max_date - pd.Timedelta(days=6)
        period_end = max_date

    elif time_period == "Last 30 Days":
        period_start = max_date - pd.Timedelta(days=29)
        period_end = max_date

    elif time_period == "Last 90 Days":
        period_start = max_date - pd.Timedelta(days=89)
        period_end = max_date

    elif time_period == "Custom":
        default_range = (min_date.date(), max_date.date())

        custom_range = st.sidebar.date_input(
            "Choose Date Range",
            value=default_range,
            min_value=min_date.date(),
            max_value=max_date.date()
        )

        if isinstance(custom_range, tuple) and len(custom_range) == 2:
            period_start = pd.Timestamp(custom_range[0])
            period_end = pd.Timestamp(custom_range[1])
        else:
            period_start = min_date
            period_end = max_date

    else:
        period_start = min_date
        period_end = max_date
else:
    time_period = "All Time"
    period_start = None
    period_end = None


# Apply filters

filtered_arrivals = arrivals.copy()

# Apply selected time period
if (
    period_start is not None
    and period_end is not None
    and "_date" in filtered_arrivals.columns
):
    _arrival_dates = pd.to_datetime(
        filtered_arrivals["_date"], errors="coerce"
    )
    filtered_arrivals = filtered_arrivals[
        _arrival_dates.between(
            pd.Timestamp(period_start),
            pd.Timestamp(period_end)
        )
    ]

if selected_crop != "All" and crop_col:
    filtered_arrivals = filtered_arrivals[
        filtered_arrivals[crop_col].astype(str) == selected_crop
    ]

if selected_mandi != "All" and mandi_col:
    filtered_arrivals = filtered_arrivals[
        filtered_arrivals[mandi_col].astype(str) == selected_mandi
    ]


# ============================================================
# KPI SECTION
# ============================================================

st.subheader("📊 Key Performance Indicators")

total_arrivals = filtered_arrivals["_quantity"].sum()

if len(filtered_arrivals) > 0:
    average_arrival = filtered_arrivals["_quantity"].mean()
else:
    average_arrival = 0


if "_modal_price" in prices.columns:
    average_price = prices["_modal_price"].mean()
else:
    average_price = np.nan


if "_msp" in prices.columns:
    average_msp = prices["_msp"].mean()
else:
    average_msp = np.nan


if (
    pd.notna(average_price)
    and pd.notna(average_msp)
    and average_msp != 0
):

    price_gap = (
        (average_price - average_msp)
        / average_msp
        * 100
    )

else:

    price_gap = np.nan


c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Arrivals",
    f"{total_arrivals:,.0f} Qtl"
)

c2.metric(
    "Average Arrival",
    f"{average_arrival:,.1f} Qtl"
)

c3.metric(
    "Average Market Price",
    f"₹{average_price:,.0f}"
    if pd.notna(average_price)
    else "N/A"
)

c4.metric(
    "Price vs MSP",
    f"{price_gap:.1f}%"
    if pd.notna(price_gap)
    else "N/A"
)


# ============================================================
# ARRIVAL TREND
# ============================================================

st.subheader("📈 Daily Arrival Trend")

if "_date" in filtered_arrivals.columns:

    daily_arrivals = (
        filtered_arrivals
        .dropna(subset=["_date"])
        .groupby("_date", as_index=False)["_quantity"]
        .sum()
    )

    if not daily_arrivals.empty:

        fig = px.line(
            daily_arrivals,
            x="_date",
            y="_quantity",
            markers=True,
            title="Daily Crop Arrivals"
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Arrival Quantity (Qtl)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("No dated arrival records available.")

else:

    st.info("Arrival date information is unavailable.")


# ============================================================
# CROP DISTRIBUTION
# ============================================================

st.subheader("🌾 Crop-wise Arrival Distribution")

if crop_col:

    crop_summary = (
        filtered_arrivals
        .groupby(crop_col, as_index=False)["_quantity"]
        .sum()
        .sort_values(
            "_quantity",
            ascending=False
        )
    )

    if not crop_summary.empty:

        fig = px.bar(
            crop_summary,
            x=crop_col,
            y="_quantity",
            title="Total Arrivals by Crop",
            text_auto=".3s"
        )

        fig.update_layout(
            xaxis_title="Crop",
            yaxis_title="Arrival Quantity (Qtl)",
            xaxis=dict(categoryorder="total descending", tickangle=0),
            height=500
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# MARKET PRICE VS MSP
# ============================================================

st.subheader("💰 Market Price vs MSP")

if "_date" in prices.columns:

    price_chart = prices.copy()

    if selected_crop != "All" and "_crop" in price_chart.columns:

        price_chart = price_chart[
            price_chart["_crop"].astype(str).str.lower()
            == selected_crop.lower()
        ]

    price_chart = price_chart.dropna(
        subset=["_date"]
    )

    price_chart = price_chart[
        [
            "_date",
            "_modal_price",
            "_msp"
        ]
    ].dropna(
        subset=["_modal_price"]
    )

    if not price_chart.empty:

        price_daily = (
            price_chart
            .groupby("_date", as_index=False)
            .agg(
                _modal_price=("_modal_price", "mean"),
                _msp=("_msp", "mean")
            )
            .sort_values("_date")
        )

        fig = px.line(
            price_daily,
            x="_date",
            y=["_modal_price", "_msp"],
            markers=True,
            title="Daily Average Market Price vs MSP"
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            height=500
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("No valid dated price records available.")

else:

    st.info("Price date information is unavailable.")


# ============================================================
# MANDI PERFORMANCE
# ============================================================

st.subheader("🏪 Mandi Performance")

if mandi_col:

    mandi_summary = (
        filtered_arrivals
        .groupby(mandi_col, as_index=False)
        .agg(
            Total_Arrivals=("_quantity", "sum"),
            Average_Arrival=("_quantity", "mean"),
            Records=("_quantity", "count")
        )
        .sort_values(
            "Total_Arrivals",
            ascending=False
        )
    )

    if not mandi_summary.empty:

        fig = px.bar(
            mandi_summary.head(15),
            x=mandi_col,
            y="Total_Arrivals",
            title="Top Mandis by Total Arrivals"
        )

        fig.update_layout(
            xaxis_title="Mandi",
            yaxis_title="Total Arrivals (Qtl)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            mandi_summary.head(15),
            use_container_width=True
        )


# ============================================================
# TRANSPORT ANALYSIS
# ============================================================

st.subheader("🚚 Logistics Performance")

if not transport.empty:

    transit_col = "_transit_hours"

    if transit_col in transport.columns:

        average_transit = transport[
            transit_col
        ].mean()

        c1, c2 = st.columns(2)

        c1.metric(
            "Average Transit Time",
            f"{average_transit:.2f} hours"
            if pd.notna(average_transit)
            else "N/A"
        )

        valid_transit = transport[
            transit_col
        ].dropna()

        if len(valid_transit) > 0:

            fig = px.histogram(
                valid_transit,
                x=transit_col,
                title="Transit Time Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# WEATHER ANALYSIS
# ============================================================

st.subheader("🌧️ Weather Impact")

if not weather.empty:

    rainfall_col = find_column(
        weather,
        ["rainfall_mm", "rainfall", "rain_mm"]
    )

    if rainfall_col:

        rainfall = clean_number(
            weather[rainfall_col]
        )

        st.metric(
            "Average Rainfall",
            f"{rainfall.mean():.2f} mm"
        )

        weather_chart = pd.DataFrame({
            "Rainfall": rainfall
        }).dropna()

        if not weather_chart.empty:

            fig = px.histogram(
                weather_chart,
                x="Rainfall",
                title="Rainfall Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# BUSINESS INSIGHTS & ALERTS
# ============================================================

st.divider()
st.subheader("💡 Business Insights & Alerts")

insight_cols = st.columns(4)

# Price alert
price_alert_count = 0
below_msp_crops = []

if "_modal_price" in prices.columns and "_msp" in prices.columns:
    price_check = prices.dropna(subset=["_modal_price", "_msp"]).copy()
    if not price_check.empty:
        price_check["gap_pct"] = (
            (price_check["_modal_price"] - price_check["_msp"])
            / price_check["_msp"].replace(0, np.nan)
            * 100
        )
        price_alert_count = int((price_check["gap_pct"] < 0).sum())

        if "_crop" in price_check.columns:
            below_msp_crops = (
                price_check.groupby("_crop")["gap_pct"]
                .mean()
                .sort_values()
            )
            below_msp_crops = [
                c for c in below_msp_crops.index
                if pd.notna(c)
            ][:3]

with insight_cols[0]:
    st.metric("⚠️ Below-MSP Records", f"{price_alert_count:,}")

# Supply alert
supply_alert = "Stable"
if "_date" in filtered_arrivals.columns and len(filtered_arrivals) > 0:
    daily_check = (
        filtered_arrivals.dropna(subset=["_date"])
        .groupby("_date")["_quantity"]
        .sum()
        .sort_index()
    )
    if len(daily_check) >= 14:
        recent = daily_check.tail(7).mean()
        previous = daily_check.iloc[-14:-7].mean()
        if previous > 0:
            change = (recent - previous) / previous * 100
            if change <= -20:
                supply_alert = "Supply Decline"
            elif change >= 20:
                supply_alert = "Supply Surge"

with insight_cols[1]:
    st.metric("📦 Supply Signal", supply_alert)

# Logistics alert
avg_transit_alert = np.nan
if not transport.empty and "_transit_hours" in transport.columns:
    avg_transit_alert = transport["_transit_hours"].mean()

with insight_cols[2]:
    st.metric(
        "🚚 Avg Transit",
        f"{avg_transit_alert:.1f} hrs"
        if pd.notna(avg_transit_alert)
        else "N/A"
    )

# Weather alert
avg_rain_alert = np.nan
if not weather.empty:
    rain_alert_col = find_column(
        weather, ["rainfall_mm", "rainfall", "rain_mm"]
    )
    if rain_alert_col:
        avg_rain_alert = clean_number(weather[rain_alert_col]).mean()

with insight_cols[3]:
    st.metric(
        "🌧️ Avg Rainfall",
        f"{avg_rain_alert:.1f} mm"
        if pd.notna(avg_rain_alert)
        else "N/A"
    )

# Human-readable insights
if below_msp_crops:
    st.warning(
        "⚠️ **Price Alert:** "
        + ", ".join(below_msp_crops)
        + " show the strongest average price pressure versus MSP."
    )

if supply_alert == "Supply Decline":
    st.warning(
        "📉 **Supply Alert:** Recent 7-day arrivals are materially below "
        "the preceding 7-day period."
    )
elif supply_alert == "Supply Surge":
    st.success(
        "📈 **Supply Signal:** Recent 7-day arrivals are materially above "
        "the preceding 7-day period."
    )
else:
    st.info("✅ **Supply Signal:** No major short-term supply shock detected.")


# ============================================================
# PRICE INTELLIGENCE
# ============================================================

st.subheader("💰 Price Intelligence")

if "_modal_price" in prices.columns and "_msp" in prices.columns:
    price_intel = prices.copy()

    if selected_crop != "All" and "_crop" in price_intel.columns:
        price_intel = price_intel[
            price_intel["_crop"].astype(str).str.lower()
            == selected_crop.lower()
        ]

    price_intel = price_intel.dropna(
        subset=["_modal_price", "_msp"]
    ).copy()

    if not price_intel.empty:
        price_intel["Price_Gap"] = (
            price_intel["_modal_price"] - price_intel["_msp"]
        )

        price_intel["Price_Gap_%"] = (
            price_intel["Price_Gap"]
            / price_intel["_msp"].replace(0, np.nan)
            * 100
        )

        p1, p2, p3, p4 = st.columns(4)

        avg_market_intel = price_intel["_modal_price"].mean()
        avg_msp_intel = price_intel["_msp"].mean()
        avg_gap_intel = price_intel["Price_Gap_%"].mean()
        below_count = int((price_intel["Price_Gap"] < 0).sum())

        p1.metric("Market Price", f"₹{avg_market_intel:,.0f}")
        p2.metric("MSP", f"₹{avg_msp_intel:,.0f}")
        p3.metric(
            "Average Price Gap",
            f"{avg_gap_intel:+.1f}%"
        )
        p4.metric("Below-MSP Records", f"{below_count:,}")

        if "_crop" in price_intel.columns:
            crop_price_intel = (
                price_intel.groupby("_crop", as_index=False)
                .agg(
                    Market_Price=("_modal_price", "mean"),
                    MSP=("_msp", "mean")
                )
            )

            crop_price_intel["Gap_%"] = (
                (crop_price_intel["Market_Price"]
                 - crop_price_intel["MSP"])
                / crop_price_intel["MSP"].replace(0, np.nan)
                * 100
            )

            fig = px.bar(
                crop_price_intel.sort_values("Gap_%"),
                x="_crop",
                y="Gap_%",
                title="Price Gap vs MSP by Crop",
                text_auto=".1f"
            )

            fig.add_hline(
                y=0,
                line_dash="dash"
            )

            fig.update_layout(
                xaxis_title="Crop",
                yaxis_title="Price Gap vs MSP (%)",
                height=450
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            display_cols = [
                "_crop", "Market_Price", "MSP", "Gap_%"
            ]

            st.dataframe(
                crop_price_intel[display_cols]
                .sort_values("Gap_%"),
                use_container_width=True
            )
    else:
        st.info("No valid price intelligence records available.")
else:
    st.info("Price intelligence data is unavailable.")


# ============================================================
# AGENTIC GRAPH AI
# ============================================================

st.divider()

st.header("🤖 Agentic Graph AI")

st.markdown(
    """
    Ask a business question in natural language. The agent converts the
    question into an intent, extracts entities, applies filters, builds an
    explainable analytical query, creates a dataframe, selects the chart
    type, renders a Plotly visualization and produces an insight summary.
    """
)

question = st.text_input(
    "💬 Ask a business question",
    placeholder="Example: Show the daily arrival trend of Wheat"
)

st.caption(
    "Pipeline: Natural Language → Intent → Entities → Filters → "
    "SQL Query → DataFrame → Chart Selection → Plotly → Insight Summary"
)


# ============================================================
# AGENT HELPER FUNCTIONS
# ============================================================

def detect_agent_intent(q):
    """Return a clear business intent from a natural-language question."""
    q = q.lower()

    if (
        ("price" in q and "msp" in q)
        or "market price" in q
        or "price vs" in q
        or "price comparison" in q
    ):
        return "Price vs MSP"

    if (
        ("arrival" in q or "arrivals" in q)
        and ("trend" in q or "daily" in q or "over time" in q)
    ):
        return "Daily Arrival Trend"

    if (
        ("highest" in q or "most" in q or "top" in q)
        and "crop" in q
    ):
        return "Top Crops by Arrivals"

    if (
        "mandi" in q
        and ("highest" in q or "top" in q or "most" in q)
    ):
        return "Top Mandis by Arrivals"

    if (
        "rain" in q
        or "rainfall" in q
        or "weather" in q
    ):
        return "Weather Impact"

    if (
        "transit" in q
        or "transport" in q
        or "logistics" in q
    ):
        return "Logistics Performance"

    return "Unknown"


def extract_crop_entity(q):
    """Extract a crop entity and map aliases to canonical crop names."""
    q_lower = q.lower()

    aliases = {
        "wheat": "Wheat",
        "gehun": "Wheat",
        "gehu": "Wheat",
        "kanak": "Wheat",
        "गेहूं": "Wheat",

        "rice": "Rice",
        "paddy": "Rice",
        "dhan": "Rice",
        "dhaan": "Rice",
        "basmati": "Rice",
        "chawal": "Rice",
        "धान": "Rice",
        "चावल": "Rice",

        "maize": "Maize",
        "corn": "Maize",
        "makka": "Maize",
        "makki": "Maize",
        "मक्का": "Maize",

        "cotton": "Cotton",
        "kapas": "Cotton",
        "narma": "Cotton",
        "कपास": "Cotton",

        "mustard": "Mustard",
        "sarso": "Mustard",
        "sarson": "Mustard",
        "सरसों": "Mustard",

        "sugarcane": "Sugarcane",
        "ganna": "Sugarcane",
        "ganne": "Sugarcane",
        "गन्ना": "Sugarcane"
    }

    # Check longer aliases first.
    for alias in sorted(aliases, key=len, reverse=True):
        if alias in q_lower:
            return aliases[alias]

    return None


def extract_mandi_entity(q, arrivals_df):
    """Try to extract a mandi name or mandi ID from the question."""
    q_lower = q.lower()

    # Prefer known mandi IDs.
    if "mandi_id" in arrivals_df.columns:
        for value in arrivals_df["mandi_id"].dropna().astype(str).unique():
            if value.lower() in q_lower:
                return value

    # Then try known mandi names if present.
    mandi_name_col = find_column(
        arrivals_df,
        ["mandi_name", "mandi"]
    )

    if mandi_name_col:
        names = (
            arrivals_df[mandi_name_col]
            .dropna()
            .astype(str)
            .unique()
        )

        for value in sorted(names, key=len, reverse=True):
            if value.lower() in q_lower:
                return value

    # Common example mentioned in the challenge.
    if "amritsar" in q_lower:
        return "Amritsar"

    return None


def extract_time_entity(q):
    """Extract a simple time-period entity from natural language."""
    q_lower = q.lower()

    if "last 7 days" in q_lower or "past 7 days" in q_lower:
        return "Last 7 Days"

    if "last 30 days" in q_lower or "past 30 days" in q_lower:
        return "Last 30 Days"

    if "last 90 days" in q_lower or "past 90 days" in q_lower:
        return "Last 90 Days"

    if "last month" in q_lower or "past month" in q_lower:
        return "Last 30 Days"

    if "last week" in q_lower or "past week" in q_lower:
        return "Last 7 Days"

    return "Current Dashboard Period"


def agent_sql(intent, crop=None, mandi=None, time_entity=None):
    """Generate an explainable SQL representation of the selected intent."""
    crop_condition = ""
    mandi_condition = ""

    if crop:
        crop_condition = (
            f" AND crop_name = '{crop}'"
        )

    if mandi:
        mandi_condition = (
            f" AND mandi_id = '{mandi}'"
        )

    if intent == "Price vs MSP":
        return (
            "SELECT date, AVG(modal_price) AS market_price, "
            "AVG(msp) AS msp "
            "FROM prices_fact "
            f"WHERE modal_price IS NOT NULL AND msp IS NOT NULL"
            f"{crop_condition}{mandi_condition} "
            "GROUP BY date ORDER BY date;"
        )

    if intent == "Daily Arrival Trend":
        return (
            "SELECT date, SUM(arrival_quantity_qtl) AS arrivals_qtl "
            "FROM arrivals_fact "
            f"WHERE arrival_quantity_qtl IS NOT NULL"
            f"{crop_condition}{mandi_condition} "
            "GROUP BY date ORDER BY date;"
        )

    if intent == "Top Crops by Arrivals":
        return (
            "SELECT crop_name, SUM(arrival_quantity_qtl) AS arrivals_qtl "
            "FROM arrivals_fact "
            "WHERE arrival_quantity_qtl IS NOT NULL "
            "GROUP BY crop_name ORDER BY arrivals_qtl DESC LIMIT 10;"
        )

    if intent == "Top Mandis by Arrivals":
        return (
            "SELECT mandi_id, SUM(arrival_quantity_qtl) AS arrivals_qtl "
            "FROM arrivals_fact "
            "WHERE arrival_quantity_qtl IS NOT NULL "
            "GROUP BY mandi_id ORDER BY arrivals_qtl DESC LIMIT 10;"
        )

    if intent == "Weather Impact":
        return (
            "SELECT date, rainfall_mm, temp_c, humidity_percent "
            "FROM weather_daily ORDER BY date;"
        )

    if intent == "Logistics Performance":
        return (
            "SELECT destination_warehouse, "
            "AVG(transit_hours) AS avg_transit_hours "
            "FROM transport_fact "
            "WHERE transit_hours IS NOT NULL "
            "GROUP BY destination_warehouse "
            "ORDER BY avg_transit_hours DESC;"
        )

    return "-- No analytical SQL generated for this question."


def apply_agent_filters(df, crop=None, mandi=None):
    """Apply extracted crop and mandi entities to a dataframe."""
    result = df.copy()

    if crop is not None and "_agent_crop" in result.columns:
        result = result[
            result["_agent_crop"].astype(str).str.lower()
            == crop.lower()
        ]

    if mandi is not None and "mandi_id" in result.columns:
        result = result[
            result["mandi_id"].astype(str).str.lower()
            == mandi.lower()
        ]

    return result


def agent_insight_summary(
    intent,
    result,
    crop=None,
    mandi=None
):
    """Create a concise data-driven business insight."""
    if result is None or result.empty:
        return "No matching records were available for this question."

    if intent == "Price vs MSP":
        market = result["_agent_modal_price"].mean()
        msp = result["_agent_msp"].mean()

        if pd.isna(market) or pd.isna(msp) or msp == 0:
            return "Price and MSP values were insufficient to calculate the gap."

        gap_pct = (market - msp) / msp * 100

        direction = "above" if gap_pct >= 0 else "below"

        crop_text = f" for {crop}" if crop else ""
        return (
            f"Average market price is ₹{market:,.0f} versus "
            f"MSP of ₹{msp:,.0f}{crop_text}, with the market price "
            f"{abs(gap_pct):.1f}% {direction} MSP."
        )

    if intent == "Daily Arrival Trend":
        if "_agent_quantity" not in result.columns:
            return "Arrival quantity was unavailable."

        daily = (
            result.dropna(subset=["_agent_date"])
            .groupby("_agent_date")["_agent_quantity"]
            .sum()
            .sort_index()
        )

        if len(daily) < 2:
            return "Not enough dated observations were available to identify a trend."

        first = daily.iloc[0]
        last = daily.iloc[-1]

        if first == 0:
            change_text = "from a zero starting point"
        else:
            change = (last - first) / first * 100
            change_text = f"a {change:+.1f}% change from the first displayed day"

        crop_text = f" for {crop}" if crop else ""
        return (
            f"Daily arrivals{crop_text} show {change_text} "
            f"across the displayed period."
        )

    if intent == "Top Crops by Arrivals":
        if "_agent_crop" not in result.columns:
            return "Crop information was unavailable."

        summary = (
            result.groupby("_agent_crop")["_agent_quantity"]
            .sum()
            .sort_values(ascending=False)
        )

        if summary.empty:
            return "No crop arrival totals were available."

        top = summary.index[0]
        value = summary.iloc[0]

        return (
            f"{top} has the highest total recorded arrivals at "
            f"{value:,.0f} Qtl."
        )

    if intent == "Top Mandis by Arrivals":
        if "mandi_id" not in result.columns:
            return "Mandi information was unavailable."

        summary = (
            result.groupby("mandi_id")["_agent_quantity"]
            .sum()
            .sort_values(ascending=False)
        )

        if summary.empty:
            return "No mandi arrival totals were available."

        top = summary.index[0]
        value = summary.iloc[0]

        return (
            f"{top} has the highest recorded arrivals at "
            f"{value:,.0f} Qtl."
        )

    if intent == "Weather Impact":
        if "rainfall_mm" in result.columns:
            rainfall = pd.to_numeric(
                result["rainfall_mm"],
                errors="coerce"
            ).mean()

            if pd.notna(rainfall):
                return (
                    f"Average daily rainfall in the weather dataset is "
                    f"{rainfall:.1f} mm. This can be used alongside "
                    f"arrival trends to assess weather-related supply pressure."
                )

        return "Weather records are available for comparison with supply trends."

    if intent == "Logistics Performance":
        if "_transit_hours" in result.columns:
            avg_transit = result["_transit_hours"].mean()

            if pd.notna(avg_transit):
                return (
                    f"Average recorded transit time is "
                    f"{avg_transit:.1f} hours. Higher transit values "
                    f"indicate potential logistics pressure."
                )

        return "Logistics records are available for transit-performance analysis."

    return "The agent could not generate a business insight."


# ============================================================
# RUN AGENT
# ============================================================

if st.button("🔎 Analyze Question"):

    if not question.strip():
        st.warning("Please enter a business question.")

    else:
        q = question.strip()

        # Load clean agent data.
        agent_arrivals, agent_prices, agent_mandi = load_agent_data()

        # Ensure mandi IDs are standardized for entity filtering.
        for df in [agent_arrivals, agent_prices]:
            if "mandi_id" in df.columns:
                df["mandi_id"] = df["mandi_id"].apply(
                    normalize_mandi_value
                )

        # --------------------------------------------------------
        # 1. NATURAL LANGUAGE
        # --------------------------------------------------------

        st.markdown("### 🗣️ 1. Natural Language Question")
        st.code(q, language="text")

        # --------------------------------------------------------
        # 2. INTENT EXTRACTION
        # --------------------------------------------------------

        intent = detect_agent_intent(q)

        # --------------------------------------------------------
        # 3. ENTITY EXTRACTION
        # --------------------------------------------------------

        crop_entity = extract_crop_entity(q)
        mandi_entity = extract_mandi_entity(q, agent_arrivals)
        time_entity = extract_time_entity(q)

        entity_col1, entity_col2, entity_col3 = st.columns(3)

        with entity_col1:
            st.metric(
                "Intent",
                intent
            )

        with entity_col2:
            st.metric(
                "Crop Entity",
                crop_entity if crop_entity else "Not specified"
            )

        with entity_col3:
            st.metric(
                "Time Entity",
                time_entity
            )

        if mandi_entity:
            st.info(f"🏪 **Mandi Entity:** {mandi_entity}")

        if intent == "Unknown":
            st.warning(
                "The agent could not confidently identify the business intent."
            )
            st.info(
                "Try: Show market price vs MSP for Wheat | "
                "Show the daily arrival trend of Wheat | "
                "Which crop has the highest total arrivals? | "
                "Which mandis have the highest arrivals?"
            )

        else:

            # ----------------------------------------------------
            # 4. FILTERS
            # ----------------------------------------------------

            st.markdown("### 🔎 4. Filters Applied")

            active_filters = []

            if crop_entity:
                active_filters.append(f"Crop = {crop_entity}")

            if mandi_entity:
                active_filters.append(f"Mandi = {mandi_entity}")

            if time_entity != "Current Dashboard Period":
                active_filters.append(f"Time = {time_entity}")

            # Also show dashboard-level filters.
            if selected_crop != "All":
                active_filters.append(
                    f"Dashboard Crop = {selected_crop}"
                )

            if selected_mandi != "All":
                active_filters.append(
                    f"Dashboard Mandi = {selected_mandi}"
                )

            if time_period != "All Time":
                active_filters.append(
                    f"Dashboard Time = {time_period}"
                )

            if active_filters:
                st.write(" • ".join(active_filters))
            else:
                st.write("No additional filters applied.")

            # ----------------------------------------------------
            # 5. SQL QUERY
            # ----------------------------------------------------

            st.markdown("### 🧾 5. Generated SQL Query")

            sql_text = agent_sql(
                intent,
                crop=crop_entity,
                mandi=mandi_entity,
                time_entity=time_entity
            )

            st.code(sql_text, language="sql")

            st.caption(
                "The SQL shown is the agent's explainable analytical query plan. "
                "The deployed app executes the equivalent operation on the "
                "clean pandas dataframes, so no external database is required."
            )

            # ----------------------------------------------------
            # 6. DATAFRAME + 7. CHART SELECTION
            # ----------------------------------------------------

            display_df = None
            fig = None
            chart_type = None
            chart_reason = None
            insight = None

            if intent == "Price vs MSP":

                result = apply_agent_filters(
                    agent_prices,
                    crop=crop_entity,
                    mandi=mandi_entity
                )

                result = result.dropna(
                    subset=[
                        "_agent_modal_price",
                        "_agent_msp"
                    ]
                )

                if "_agent_date" in result.columns:
                    result = result.dropna(
                        subset=["_agent_date"]
                    )

                if result.empty:
                    st.warning(
                        "No valid price and MSP records were found "
                        "for this question."
                    )

                else:
                    result_daily = (
                        result
                        .groupby("_agent_date", as_index=False)
                        .agg(
                            _agent_modal_price=(
                                "_agent_modal_price",
                                "mean"
                            ),
                            _agent_msp=(
                                "_agent_msp",
                                "mean"
                            )
                        )
                        .sort_values("_agent_date")
                    )

                    chart_type = "Line chart"
                    chart_reason = (
                        "Time-series comparison of daily market price "
                        "against MSP."
                    )

                    display_df = result_daily.copy()
                    display_df["_agent_date"] = (
                        display_df["_agent_date"].astype(str)
                    )

                    chart_df = result_daily.copy()

                    fig = px.line(
                        chart_df,
                        x="_agent_date",
                        y=[
                            "_agent_modal_price",
                            "_agent_msp"
                        ],
                        markers=True,
                        title=(
                            "Daily Average Market Price vs MSP"
                            + (
                                f" — {crop_entity}"
                                if crop_entity
                                else ""
                            )
                        )
                    )

                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Price (₹)",
                        height=500
                    )

                    insight = agent_insight_summary(
                        intent,
                        result,
                        crop=crop_entity,
                        mandi=mandi_entity
                    )

            elif intent == "Daily Arrival Trend":

                result = apply_agent_filters(
                    agent_arrivals,
                    crop=crop_entity,
                    mandi=mandi_entity
                )

                result = result.dropna(
                    subset=["_agent_date"]
                )

                if result.empty:
                    st.warning(
                        "No valid dated arrival records were found."
                    )

                else:
                    daily = (
                        result
                        .groupby(
                            "_agent_date",
                            as_index=False
                        )["_agent_quantity"]
                        .sum()
                        .sort_values("_agent_date")
                    )

                    # Respect the requested natural-language period.
                    if time_entity == "Last 7 Days":
                        daily = daily.tail(7)
                    elif time_entity == "Last 30 Days":
                        daily = daily.tail(30)
                    elif time_entity == "Last 90 Days":
                        daily = daily.tail(90)
                    elif time_entity == "Current Dashboard Period":
                        # Use dashboard period when it is not All Time.
                        if time_period == "Last 7 Days":
                            daily = daily.tail(7)
                        elif time_period == "Last 30 Days":
                            daily = daily.tail(30)
                        elif time_period == "Last 90 Days":
                            daily = daily.tail(90)

                    if daily.empty:
                        st.warning("No arrival records match the selected period.")
                    else:
                        chart_type = "Line chart"
                        chart_reason = (
                            "A line chart is selected because arrivals "
                            "are an ordered daily time series."
                        )

                        display_df = daily.copy()
                        display_df["_agent_date"] = (
                            display_df["_agent_date"].astype(str)
                        )

                        chart_df = daily.copy()

                        fig = px.line(
                            chart_df,
                            x="_agent_date",
                            y="_agent_quantity",
                            markers=True,
                            title=(
                                "Daily Arrival Trend"
                                + (
                                    f" — {crop_entity}"
                                    if crop_entity
                                    else ""
                                )
                            )
                        )

                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Arrivals (Qtl)",
                            height=500
                        )

                        insight = agent_insight_summary(
                            intent,
                            result,
                            crop=crop_entity,
                            mandi=mandi_entity
                        )

            elif intent == "Top Crops by Arrivals":

                result = agent_arrivals.copy()

                if "_agent_quantity" not in result.columns:
                    result["_agent_quantity"] = np.nan

                summary = (
                    result.dropna(
                        subset=["_agent_quantity"]
                    )
                    .groupby(
                        "_agent_crop",
                        as_index=False
                    )["_agent_quantity"]
                    .sum()
                    .sort_values(
                        "_agent_quantity",
                        ascending=False
                    )
                    .head(10)
                )

                if summary.empty:
                    st.warning("No crop arrival data is available.")
                else:
                    chart_type = "Horizontal bar chart"
                    chart_reason = (
                        "A ranked bar chart is selected because the "
                        "question asks for a category ranking."
                    )

                    display_df = summary.copy()
                    chart_df = summary.copy()

                    fig = px.bar(
                        chart_df,
                        x="_agent_crop",
                        y="_agent_quantity",
                        title="Top Crops by Total Arrivals",
                        text_auto=".3s"
                    )

                    fig.update_layout(
                        xaxis_title="Crop",
                        yaxis_title="Total Arrivals (Qtl)",
                        xaxis=dict(categoryorder="total descending"),
                        height=500
                    )

                    insight = agent_insight_summary(
                        intent,
                        agent_arrivals,
                        crop=crop_entity,
                        mandi=mandi_entity
                    )

            elif intent == "Top Mandis by Arrivals":

                result = apply_agent_filters(
                    agent_arrivals,
                    crop=crop_entity,
                    mandi=None
                )

                if "mandi_id" not in result.columns:
                    st.warning("Mandi information is unavailable.")
                else:
                    summary = (
                        result.dropna(
                            subset=["_agent_quantity"]
                        )
                        .groupby(
                            "mandi_id",
                            as_index=False
                        )["_agent_quantity"]
                        .sum()
                        .sort_values(
                            "_agent_quantity",
                            ascending=False
                        )
                        .head(10)
                    )

                    if summary.empty:
                        st.warning("No mandi arrival data is available.")
                    else:
                        chart_type = "Horizontal bar chart"
                        chart_reason = (
                            "A ranked bar chart is selected to compare "
                            "mandis by total arrivals."
                        )

                        display_df = summary.copy()
                        chart_df = summary.copy()

                        fig = px.bar(
                            chart_df,
                            x="mandi_id",
                            y="_agent_quantity",
                            title="Top 10 Mandis by Total Arrivals",
                            text_auto=".3s"
                        )

                        fig.update_layout(
                            xaxis_title="Mandi",
                            yaxis_title="Total Arrivals (Qtl)",
                            xaxis_tickangle=-45,
                            height=500
                        )

                        insight = agent_insight_summary(
                            intent,
                            result,
                            crop=crop_entity,
                            mandi=mandi_entity
                        )

            elif intent == "Weather Impact":

                weather_agent = weather.copy()

                rain_col = find_column(
                    weather_agent,
                    ["rainfall_mm", "rainfall", "rain_mm"]
                )

                if rain_col:
                    weather_agent["rainfall_mm"] = clean_number(
                        weather_agent[rain_col]
                    )

                if "date" in weather_agent.columns:
                    weather_agent["date"] = pd.to_datetime(
                        weather_agent["date"],
                        errors="coerce"
                    )

                result = weather_agent.dropna(
                    subset=["rainfall_mm"]
                    if "rainfall_mm" in weather_agent.columns
                    else []
                )

                if result.empty:
                    st.warning("No weather records are available.")
                else:
                    chart_type = "Histogram"
                    chart_reason = (
                        "A histogram is selected to show the distribution "
                        "of rainfall observations."
                    )

                    display_df = result.head(100).copy()
                    chart_df = result.copy()

                    fig = px.histogram(
                        chart_df,
                        x="rainfall_mm",
                        title="Rainfall Distribution"
                    )

                    fig.update_layout(
                        xaxis_title="Rainfall (mm)",
                        yaxis_title="Number of Records",
                        height=500
                    )

                    insight = agent_insight_summary(
                        intent,
                        result
                    )

            elif intent == "Logistics Performance":

                result = transport.copy()

                if "_transit_hours" not in result.columns:
                    transit_col = find_column(
                        result,
                        [
                            "transit_hours",
                            "transit_time",
                            "travel_hours"
                        ]
                    )

                    if transit_col:
                        result["_transit_hours"] = clean_number(
                            result[transit_col]
                        )

                if "_transit_hours" not in result.columns:
                    st.warning(
                        "Transit-time information is unavailable."
                    )
                else:
                    result = result.dropna(
                        subset=["_transit_hours"]
                    )

                    warehouse_col = find_column(
                        result,
                        [
                            "destination_warehouse",
                            "warehouse"
                        ]
                    )

                    if warehouse_col:
                        summary = (
                            result.groupby(
                                warehouse_col,
                                as_index=False
                            )["_transit_hours"]
                            .mean()
                            .sort_values(
                                "_transit_hours",
                                ascending=False
                            )
                        )

                        display_df = summary.copy()
                        chart_df = summary.copy()

                        chart_type = "Bar chart"
                        chart_reason = (
                            "A bar chart is selected to compare average "
                            "transit performance across warehouses."
                        )

                        fig = px.bar(
                            chart_df,
                            x=warehouse_col,
                            y="_transit_hours",
                            title="Average Transit Time by Warehouse",
                            text_auto=".1f"
                        )

                        fig.update_layout(
                            xaxis_title="Warehouse",
                            yaxis_title="Average Transit Time (hours)",
                            height=500
                        )

                    else:
                        display_df = result[["_transit_hours"]].head(100)
                        chart_df = result

                        chart_type = "Histogram"
                        chart_reason = (
                            "A histogram is selected to show the "
                            "distribution of transit times."
                        )

                        fig = px.histogram(
                            chart_df,
                            x="_transit_hours",
                            title="Transit Time Distribution"
                        )

                        fig.update_layout(
                            xaxis_title="Transit Time (hours)",
                            yaxis_title="Number of Records",
                            height=500
                        )

                    insight = agent_insight_summary(
                        intent,
                        result
                    )

            # ----------------------------------------------------
            # SHOW AGENT EXECUTION
            # ----------------------------------------------------

            if fig is not None and display_df is not None:

                st.markdown("### 🧠 6. DataFrame")

                st.dataframe(
                    display_df.head(20),
                    use_container_width=True
                )

                st.caption(
                    f"Showing up to 20 rows from the agent's analytical result "
                    f"({len(display_df):,} rows before display limiting)."
                )

                st.markdown("### 📊 7. Chart Selection")

                c1, c2 = st.columns(2)

                with c1:
                    st.success(
                        f"**Selected chart:** {chart_type}"
                    )

                with c2:
                    st.info(chart_reason)

                st.markdown("### 📈 8. Plotly Visualization")

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                st.markdown("### 💡 9. Insight Summary")

                st.success(
                    f"**Business Insight:** {insight}"
                )

                st.caption(
                    "Agent execution complete: natural language → "
                    "intent → entities → filters → SQL → dataframe → "
                    "chart selection → Plotly → insight summary."
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌾 Agri Mandi-to-Market Supply Chain Optimizer | "
    "TransOrg AgentIQ Datathon – Track 3"
)