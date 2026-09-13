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

def normalize_crop_value(x):
    if pd.isna(x):
        return np.nan
    return CROP_MAP.get(str(x).strip().lower(), np.nan)


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

    crop_values = sorted(
        arrivals[crop_col]
        .dropna()
        .astype(str)
        .unique()
    )

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


# Apply filters
filtered_arrivals = arrivals.copy()

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
# AGENTIC AI
# ============================================================

st.divider()

st.header("🤖 Agentic Graph AI")

st.markdown(
    """
    Ask a business question in natural language and the agent will
    select an appropriate analytical view and generate a business insight.
    """
)


question = st.text_input(
    "💬 Ask a business question",
    placeholder="Example: Show market price vs MSP for Wheat"
)


# ============================================================
# AGENT
# ============================================================

if st.button("🔎 Analyze Question"):

    if not question.strip():

        st.warning("Please enter a question.")

    else:

        q = question.lower().strip()

        agent_arrivals, agent_prices, agent_mandi = load_agent_data()

        # ----------------------------------------------------
        # EXTRACT CROP
        # ----------------------------------------------------

        known_crops = [
            "wheat",
            "rice",
            "maize",
            "corn",
            "cotton",
            "mustard",
            "sugarcane",
            "paddy",
            "basmati"
        ]

        detected_crop = None

        for crop in known_crops:

            if crop in q:

                detected_crop = crop
                break


        # ----------------------------------------------------
        # PRICE VS MSP
        # ----------------------------------------------------

        if (
            "price" in q
            and "msp" in q
        ):

            result = agent_prices.copy()

            if detected_crop and "_agent_crop" in result.columns:

                result = result[
                    result["_agent_crop"]
                    .astype(str)
                    .str.contains(
                        detected_crop,
                        case=False,
                        na=False
                    )
                ]

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

                result = result.sort_values(
                    "_agent_date"
                )

            if result.empty:

                st.warning(
                    "No valid price and MSP records were found for this question."
                )

            else:

                st.success(
                    "📊 Agent selected: Market Price vs MSP line chart"
                )

                result_daily = (
                    result
                    .groupby("_agent_date", as_index=False)
                    .agg(
                        _agent_modal_price=("_agent_modal_price", "mean"),
                        _agent_msp=("_agent_msp", "mean")
                    )
                    .sort_values("_agent_date")
                )

                fig = px.line(
                    result_daily,
                    x="_agent_date",
                    y=[
                        "_agent_modal_price",
                        "_agent_msp"
                    ],
                    markers=True,
                    title=(
                        "Daily Average Market Price vs MSP"
                        + (
                            f" — {detected_crop.title()}"
                            if detected_crop
                            else ""
                        )
                    )
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

                avg_market = result[
                    "_agent_modal_price"
                ].mean()

                avg_msp_value = result[
                    "_agent_msp"
                ].mean()

                gap = avg_market - avg_msp_value

                gap_percent = (
                    gap / avg_msp_value * 100
                    if avg_msp_value != 0
                    else np.nan
                )

                if gap > 0:

                    insight = (
                        f"Market price is approximately "
                        f"{abs(gap_percent):.1f}% above MSP."
                    )

                else:

                    insight = (
                        f"Market price is approximately "
                        f"{abs(gap_percent):.1f}% below MSP."
                    )

                st.info(
                    f"💡 **Business Insight:** {insight}"
                )


        # ----------------------------------------------------
        # DAILY ARRIVAL TREND
        # ----------------------------------------------------

        elif (
            "arrival" in q
            or "arrivals" in q
        ) and (
            "trend" in q
            or "daily" in q
        ):

            result = agent_arrivals.copy()

            if detected_crop and "_agent_crop" in result.columns:

                result = result[
                    result["_agent_crop"]
                    .astype(str)
                    .str.contains(
                        detected_crop,
                        case=False,
                        na=False
                    )
                ]

            if "_agent_date" not in result.columns:

                st.warning(
                    "No usable arrival date field was found."
                )

            else:

                result = result.dropna(
                    subset=["_agent_date"]
                )

                daily = (
                    result
                    .groupby(
                        "_agent_date",
                        as_index=False
                    )["_agent_quantity"]
                    .sum()
                )

                daily = daily.sort_values(
                    "_agent_date"
                )

                if not daily.empty:

                    daily = daily.tail(30)

                    st.success(
                        "📈 Agent selected: Daily Arrival Trend"
                    )

                    fig = px.line(
                        daily,
                        x="_agent_date",
                        y="_agent_quantity",
                        markers=True,
                        title=(
                            "Daily Arrival Trend"
                            + (
                                f" — {detected_crop.title()}"
                                if detected_crop
                                else ""
                            )
                        )
                    )

                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Arrivals (Qtl)"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    st.info(
                        "💡 **Business Insight:** "
                        "The chart highlights the latest 30-day arrival movement "
                        "and can help identify supply increases or declines."
                    )


        # ----------------------------------------------------
        # HIGHEST ARRIVALS BY CROP
        # ----------------------------------------------------

        elif (
            "highest" in q
            or "most" in q
        ) and (
            "crop" in q
            or "arrivals" in q
        ):

            if "_agent_crop" in agent_arrivals.columns:

                summary = (
                    agent_arrivals
                    .groupby(
                        "_agent_crop",
                        as_index=False
                    )["_agent_quantity"]
                    .sum()
                    .sort_values(
                        "_agent_quantity",
                        ascending=False
                    )
                )

                summary = summary.head(10)

                st.success(
                    "📊 Agent selected: Crop Arrival Ranking"
                )

                fig = px.bar(
                    summary,
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

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                if not summary.empty:

                    top_crop = summary.iloc[0][
                        "_agent_crop"
                    ]

                    st.info(
                        f"💡 **Business Insight:** "
                        f"{str(top_crop).title()} has the highest "
                        f"total recorded arrivals in the analytical dataset."
                    )


        # ----------------------------------------------------
        # HIGHEST MANDIS
        # ----------------------------------------------------

        elif (
            "mandi" in q
            and (
                "highest" in q
                or "top" in q
                or "most" in q
            )
        ):

            mandi_col_agent = find_column(
                agent_arrivals,
                [
                    "mandi_name",
                    "mandi",
                    "mandi_id"
                ]
            )

            if mandi_col_agent:

                summary = (
                    agent_arrivals
                    .groupby(
                        mandi_col_agent,
                        as_index=False
                    )["_agent_quantity"]
                    .sum()
                    .sort_values(
                        "_agent_quantity",
                        ascending=False
                    )
                    .head(10)
                )

                st.success(
                    "📊 Agent selected: Mandi Arrival Ranking"
                )

                fig = px.bar(
                    summary,
                    x=mandi_col_agent,
                    y="_agent_quantity",
                    title="Top Mandis by Total Arrivals"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------

        else:

            st.info(
                """
                🤖 **Agent could not confidently map the question.**

                Try questions such as:

                - Show market price vs MSP for Wheat
                - Show the daily arrival trend of Wheat
                - Which crop has the highest total arrivals?
                - Which mandis have the highest arrivals?
                """
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌾 Agri Mandi-to-Market Supply Chain Optimizer | "
    "TransOrg AgentIQ Datathon – Track 3"
)