# ============================================================
# TRANSORG AG RITECH DATATHON
# MANDI-TO-MARKET SUPPLY CHAIN OPTIMIZER
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Mandi-to-Market Optimizer",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parents[1]

PROCESSED = BASE / "data" / "processed"
ANALYTICS = PROCESSED / "analytics"
INSIGHTS = PROCESSED / "insights"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 0.1rem;
}

.subtitle {
    color: #8b95a7;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

.section-header {
    font-size: 1.45rem;
    font-weight: 750;
    margin-top: 1.8rem;
    margin-bottom: 0.8rem;
}

.info-box {
    padding: 14px 18px;
    border-radius: 10px;
    background: rgba(49, 51, 63, 0.25);
    border: 1px solid rgba(128,128,128,0.2);
    margin-bottom: 15px;
}

.alert-box {
    padding: 15px;
    border-radius: 10px;
    margin: 8px 0;
    border-left: 5px solid;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_csv_safe(path):
    """Read a CSV if it exists."""
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def numeric(df, columns):
    """Convert selected columns to numeric."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def date_column(df, col="date"):
    """Convert a date column safely."""
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def format_number(value):
    if pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def format_currency(value):
    if pd.isna(value):
        return "—"
    return f"₹{value:,.0f}"


def format_percent(value):
    if pd.isna(value):
        return "—"
    return f"{value:.1f}%"


def empty_message(message):
    st.info(message)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_all_data():

    arrivals = read_csv_safe(PROCESSED / "arrivals_fact.csv")
    prices = read_csv_safe(PROCESSED / "prices_fact.csv")
    transport = read_csv_safe(PROCESSED / "transport_fact.csv")
    mandi = read_csv_safe(PROCESSED / "mandi_dim.csv")
    weather = read_csv_safe(PROCESSED / "weather_daily.csv")

    mandi_health = read_csv_safe(
        INSIGHTS / "mandi_health_scores.csv"
    )

    mandi_kpi = read_csv_safe(
        ANALYTICS / "mandi_kpi.csv"
    )

    crop_kpi = read_csv_safe(
        ANALYTICS / "crop_kpi.csv"
    )

    daily_kpi = read_csv_safe(
        ANALYTICS / "daily_arrivals.csv"
    )

    return (
        arrivals,
        prices,
        transport,
        mandi,
        weather,
        mandi_health,
        mandi_kpi,
        crop_kpi,
        daily_kpi
    )


(
    arrivals,
    prices,
    transport,
    mandi,
    weather,
    mandi_health,
    mandi_kpi,
    crop_kpi,
    daily_kpi
) = load_all_data()


# ============================================================
# DATA PREPARATION
# ============================================================

# Dates

arrivals = date_column(arrivals)
prices = date_column(prices)
transport = date_column(transport)
weather = date_column(weather)


# Numeric fields

arrivals = numeric(
    arrivals,
    ["arrival_quantity_qtl", "farmer_count"]
)

prices = numeric(
    prices,
    ["modal_price", "msp", "min_price", "max_price"]
)

transport = numeric(
    transport,
    [
        "transit_hours",
        "distance_km",
        "distance",
        "delay_hours"
    ]
)

weather = numeric(
    weather,
    [
        "temp_c",
        "rainfall_mm",
        "humidity_percent"
    ]
)


# ============================================================
# FALLBACK: CREATE QUANTITY IF NEEDED
# ============================================================

if "arrival_quantity_qtl" not in arrivals.columns:

    if "arrival_quantity" in arrivals.columns:

        raw_qty = pd.to_numeric(
            arrivals["arrival_quantity"],
            errors="coerce"
        )

        if "unit" in arrivals.columns:

            units = (
                arrivals["unit"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            factors = units.map({
                "kg": 0.01,
                "kgs": 0.01,
                "kilo": 0.01,
                "q": 1,
                "qtl": 1,
                "quintal": 1,
                "quintals": 1,
                "mt": 10,
                "t": 10,
                "tonne": 10,
                "tonnes": 10
            })

            arrivals["arrival_quantity_qtl"] = (
                raw_qty * factors
            )

        else:

            arrivals["arrival_quantity_qtl"] = raw_qty


# ============================================================
# PRICE INTELLIGENCE DATA
# ============================================================

if {"modal_price", "msp"}.issubset(prices.columns):

    price_valid = prices.dropna(
        subset=["modal_price", "msp"]
    ).copy()

    price_valid = price_valid[
        price_valid["msp"] > 0
    ]

    if len(price_valid) > 0:

        price_valid["msp_gap"] = (
            price_valid["modal_price"]
            - price_valid["msp"]
        )

        price_valid["msp_gap_pct"] = (
            price_valid["msp_gap"]
            / price_valid["msp"]
        ) * 100

        price_valid["below_msp"] = (
            price_valid["modal_price"]
            < price_valid["msp"]
        )

    else:

        price_valid = pd.DataFrame()

else:

    price_valid = pd.DataFrame()


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🌾 Mandi-to-Market Supply Chain Optimizer'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AgriTech Intelligence Platform • Prices • MSP • Arrivals • Logistics • Weather'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Dashboard Controls")

st.sidebar.caption(
    "Use these filters to explore the mandi ecosystem."
)


# ------------------------------------------------------------
# CROP FILTER
# ------------------------------------------------------------

crop_options = ["All"]

if "crop_name" in arrivals.columns:

    crop_values = sorted(
        arrivals["crop_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    crop_options += crop_values


selected_crop = st.sidebar.selectbox(
    "🌾 Crop",
    crop_options
)


# ------------------------------------------------------------
# MANDI FILTER
# ------------------------------------------------------------

mandi_options = ["All"]

if "mandi_id" in arrivals.columns:

    mandi_values = sorted(
        arrivals["mandi_id"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    mandi_options += mandi_values


selected_mandi = st.sidebar.selectbox(
    "🏪 Mandi",
    mandi_options
)


# ------------------------------------------------------------
# DATE FILTER
# ------------------------------------------------------------

all_dates = []

for df in [arrivals, prices, transport, weather]:

    if "date" in df.columns:

        values = df["date"].dropna()

        if len(values) > 0:
            all_dates.extend(values.tolist())


if all_dates:

    min_date = min(all_dates)
    max_date = max(all_dates)

    selected_dates = st.sidebar.date_input(
        "📅 Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )

    if isinstance(selected_dates, tuple):

        if len(selected_dates) == 2:

            start_date = pd.Timestamp(
                selected_dates[0]
            )

            end_date = (
                pd.Timestamp(selected_dates[1])
                + pd.Timedelta(days=1)
            )

        else:

            start_date = min_date
            end_date = max_date + pd.Timedelta(days=1)

    else:

        start_date = min_date
        end_date = max_date + pd.Timedelta(days=1)

else:

    start_date = None
    end_date = None


# ============================================================
# APPLY FILTERS
# ============================================================

fa = arrivals.copy()
fp = prices.copy()
ft = transport.copy()
fw = weather.copy()


# Crop filter

if selected_crop != "All":

    if "crop_name" in fa.columns:

        fa = fa[
            fa["crop_name"].astype(str)
            == selected_crop
        ]

    if "crop_name" in fp.columns:

        fp = fp[
            fp["crop_name"].astype(str)
            == selected_crop
        ]


# Mandi filter

if selected_mandi != "All":

    if "mandi_id" in fa.columns:

        fa = fa[
            fa["mandi_id"].astype(str)
            == selected_mandi
        ]

    if "mandi_id" in fp.columns:

        fp = fp[
            fp["mandi_id"].astype(str)
            == selected_mandi
        ]

    if "mandi_id" in ft.columns:

        ft = ft[
            ft["mandi_id"].astype(str)
            == selected_mandi
        ]


# Date filter

if start_date is not None:

    if "date" in fa.columns:

        fa = fa[
            (fa["date"] >= start_date)
            &
            (fa["date"] < end_date)
        ]

    if "date" in fp.columns:

        fp = fp[
            (fp["date"] >= start_date)
            &
            (fp["date"] < end_date)
        ]

    if "date" in ft.columns:

        ft = ft[
            (ft["date"] >= start_date)
            &
            (ft["date"] < end_date)
        ]

    if "date" in fw.columns:

        fw = fw[
            (fw["date"] >= start_date)
            &
            (fw["date"] < end_date)
        ]


# Recalculate filtered price intelligence

if {"modal_price", "msp"}.issubset(fp.columns):

    fp_valid = fp.dropna(
        subset=["modal_price", "msp"]
    ).copy()

    fp_valid = fp_valid[
        fp_valid["msp"] > 0
    ]

    if len(fp_valid) > 0:

        fp_valid["msp_gap"] = (
            fp_valid["modal_price"]
            - fp_valid["msp"]
        )

        fp_valid["msp_gap_pct"] = (
            fp_valid["msp_gap"]
            / fp_valid["msp"]
        ) * 100

        fp_valid["below_msp"] = (
            fp_valid["modal_price"]
            < fp_valid["msp"]
        )

    else:

        fp_valid = pd.DataFrame()

else:

    fp_valid = pd.DataFrame()


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-header">'
    '📊 Executive Overview'
    '</div>',
    unsafe_allow_html=True
)


# Total arrivals

if "arrival_quantity_qtl" in fa.columns:

    total_arrivals = fa[
        "arrival_quantity_qtl"
    ].sum()

else:

    total_arrivals = np.nan


# Average modal price

if (
    "modal_price" in fp.columns
    and len(fp) > 0
):

    avg_modal_price = fp[
        "modal_price"
    ].mean()

else:

    avg_modal_price = np.nan


# Average MSP gap

if len(fp_valid) > 0:

    avg_msp_gap = fp_valid[
        "msp_gap_pct"
    ].mean()

else:

    avg_msp_gap = np.nan


# Price crash / below MSP rate

if len(fp_valid) > 0:

    price_crash_rate = (
        fp_valid["below_msp"].mean()
        * 100
    )

else:

    price_crash_rate = np.nan


# Average transit

if "transit_hours" in ft.columns:

    avg_transit = ft[
        "transit_hours"
    ].mean()

else:

    avg_transit = np.nan


# Delay rate
# Transparent operational rule:
# transit > 12 hours = delayed
if "transit_hours" in ft.columns:

    transit_valid = ft[
        "transit_hours"
    ].dropna()

    if len(transit_valid) > 0:

        delay_rate = (
            (transit_valid > 12).mean()
            * 100
        )

    else:

        delay_rate = np.nan

else:

    delay_rate = np.nan


# KPI cards

c1, c2, c3, c4, c5, c6 = st.columns(6)


with c1:

    st.metric(
        "🌾 Total Arrivals",
        f"{total_arrivals:,.0f} QTL"
        if pd.notna(total_arrivals)
        else "—"
    )


with c2:

    st.metric(
        "💰 Avg Modal Price",
        format_currency(avg_modal_price)
    )


with c3:

    st.metric(
        "📈 Avg MSP Gap",
        format_percent(avg_msp_gap)
    )


with c4:

    st.metric(
        "🚨 Price Crash Rate",
        format_percent(price_crash_rate),
        help="Percentage of valid price observations where modal price is below MSP."
    )


with c5:

    st.metric(
        "🚚 Avg Transit",
        f"{avg_transit:.1f} hrs"
        if pd.notna(avg_transit)
        else "—"
    )


with c6:

    st.metric(
        "⏱️ Delay Rate",
        format_percent(delay_rate),
        help="Operational definition used here: transit time greater than 12 hours."
    )


st.caption(
    "Price crash rate = below-MSP observations. "
    "Delay rate = trips with transit time > 12 hours."
)


# ============================================================
# EXECUTIVE STATUS
# ============================================================

st.markdown(
    '<div class="info-box">'
    '💡 <b>Executive Signal:</b> '
    'Use the sections below to move from overall performance '
    'to price risk, supply-chain bottlenecks and weather impact.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# PRICE INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-header">'
    '💰 Price Intelligence'
    '</div>',
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# PRICE VS MSP TREND
# ------------------------------------------------------------

if (
    len(fp_valid) > 0
    and "date" in fp_valid.columns
):

    price_daily = (
        fp_valid
        .groupby("date", as_index=False)
        .agg(
            modal_price=("modal_price", "mean"),
            msp=("msp", "mean")
        )
        .sort_values("date")
    )

    fig_price = go.Figure()

    fig_price.add_trace(
        go.Scatter(
            x=price_daily["date"],
            y=price_daily["modal_price"],
            mode="lines",
            name="Market Modal Price"
        )
    )

    fig_price.add_trace(
        go.Scatter(
            x=price_daily["date"],
            y=price_daily["msp"],
            mode="lines",
            name="MSP",
            line=dict(dash="dash")
        )
    )

    fig_price.update_layout(
        title="Market Price vs MSP",
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        hovermode="x unified",
        height=430
    )

    st.plotly_chart(
        fig_price,
        use_container_width=True
    )

else:

    empty_message(
        "Price/MSP data is not available for the selected filters."
    )


# ------------------------------------------------------------
# PRICE GAP + CROP
# ------------------------------------------------------------

p1, p2 = st.columns(2)


with p1:

    if (
        len(fp_valid) > 0
        and "crop_name" in fp_valid.columns
    ):

        crop_price = (
            fp_valid
            .groupby("crop_name", as_index=False)
            .agg(
                avg_modal_price=("modal_price", "mean"),
                avg_msp=("msp", "mean")
            )
        )

        crop_price["msp_gap_pct"] = (
            (
                crop_price["avg_modal_price"]
                - crop_price["avg_msp"]
            )
            / crop_price["avg_msp"]
        ) * 100

        crop_price = crop_price.sort_values(
            "msp_gap_pct"
        )

        fig_gap = px.bar(
            crop_price,
            x="msp_gap_pct",
            y="crop_name",
            orientation="h",
            title="MSP Gap by Crop (%)",
            labels={
                "msp_gap_pct": "MSP Gap (%)",
                "crop_name": "Crop"
            }
        )

        fig_gap.add_vline(
            x=0,
            line_dash="dash"
        )

        st.plotly_chart(
            fig_gap,
            use_container_width=True
        )

    else:

        empty_message(
            "Crop-level price data unavailable."
        )


with p2:

    if (
        len(fp_valid) > 0
        and "crop_name" in fp_valid.columns
    ):

        crash_crop = (
            fp_valid
            .groupby("crop_name", as_index=False)
            .agg(
                crash_rate=("below_msp", "mean"),
                observations=("below_msp", "count")
            )
        )

        crash_crop["crash_rate"] *= 100

        crash_crop = crash_crop.sort_values(
            "crash_rate",
            ascending=False
        )

        fig_crash = px.bar(
            crash_crop,
            x="crop_name",
            y="crash_rate",
            title="Below-MSP / Price Crash Rate",
            labels={
                "crop_name": "Crop",
                "crash_rate": "Below MSP (%)"
            }
        )

        st.plotly_chart(
            fig_crash,
            use_container_width=True
        )

    else:

        empty_message(
            "Price crash analysis unavailable."
        )


# ------------------------------------------------------------
# TOP PRICE-RISK MANDIS
# ------------------------------------------------------------

if (
    len(fp_valid) > 0
    and "mandi_id" in fp_valid.columns
):

    mandi_price_risk = (
        fp_valid
        .groupby("mandi_id", as_index=False)
        .agg(
            avg_modal_price=("modal_price", "mean"),
            avg_msp=("msp", "mean"),
            below_msp_rate=("below_msp", "mean")
        )
    )

    mandi_price_risk["msp_gap_pct"] = (
        (
            mandi_price_risk["avg_modal_price"]
            - mandi_price_risk["avg_msp"]
        )
        / mandi_price_risk["avg_msp"]
    ) * 100

    mandi_price_risk["below_msp_rate"] *= 100

    mandi_price_risk = mandi_price_risk.sort_values(
        "msp_gap_pct"
    ).head(10)

    st.subheader("🚨 Top Price-Risk Mandis")

    st.dataframe(
        mandi_price_risk.round(2),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# SUPPLY CHAIN
# ============================================================

st.markdown(
    '<div class="section-header">'
    '🚚 Supply Chain Intelligence'
    '</div>',
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# DAILY ARRIVALS
# ------------------------------------------------------------

if (
    "date" in fa.columns
    and "arrival_quantity_qtl" in fa.columns
):

    daily = (
        fa
        .groupby("date", as_index=False)
        ["arrival_quantity_qtl"]
        .sum()
        .sort_values("date")
    )

    fig_supply = px.area(
        daily,
        x="date",
        y="arrival_quantity_qtl",
        title="Daily Crop Arrival Trend",
        labels={
            "date": "Date",
            "arrival_quantity_qtl": "Arrivals (QTL)"
        }
    )

    fig_supply.update_layout(
        height=420,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_supply,
        use_container_width=True
    )


# ------------------------------------------------------------
# CROP DISTRIBUTION
# ------------------------------------------------------------

s1, s2 = st.columns(2)


with s1:

    if (
        "crop_name" in fa.columns
        and "arrival_quantity_qtl" in fa.columns
    ):

        crop_arrivals = (
            fa
            .groupby("crop_name", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
            .sort_values(
                "arrival_quantity_qtl",
                ascending=False
            )
        )

        fig_crop = px.bar(
            crop_arrivals,
            x="crop_name",
            y="arrival_quantity_qtl",
            title="Arrival Volume by Crop",
            labels={
                "crop_name": "Crop",
                "arrival_quantity_qtl": "Arrivals (QTL)"
            }
        )

        st.plotly_chart(
            fig_crop,
            use_container_width=True
        )


with s2:

    if (
        "mandi_id" in fa.columns
        and "arrival_quantity_qtl" in fa.columns
    ):

        mandi_arrivals = (
            fa
            .groupby("mandi_id", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
            .sort_values(
                "arrival_quantity_qtl",
                ascending=False
            )
            .head(10)
        )

        fig_mandi = px.bar(
            mandi_arrivals,
            x="arrival_quantity_qtl",
            y="mandi_id",
            orientation="h",
            title="Top 10 Mandis by Arrivals",
            labels={
                "mandi_id": "Mandi",
                "arrival_quantity_qtl": "Arrivals (QTL)"
            }
        )

        st.plotly_chart(
            fig_mandi,
            use_container_width=True
        )


# ------------------------------------------------------------
# LOGISTICS
# ------------------------------------------------------------

l1, l2 = st.columns(2)


with l1:

    if (
        "transit_hours" in ft.columns
        and len(ft) > 0
    ):

        transit_data = ft[
            "transit_hours"
        ].dropna()

        if len(transit_data) > 0:

            fig_transit = px.histogram(
                transit_data,
                x="transit_hours",
                nbins=30,
                title="Transit Time Distribution",
                labels={
                    "transit_hours": "Transit Time (hours)"
                }
            )

            fig_transit.add_vline(
                x=12,
                line_dash="dash",
                annotation_text="12h delay threshold"
            )

            st.plotly_chart(
                fig_transit,
                use_container_width=True
            )


with l2:

    if (
        "destination_warehouse" in ft.columns
        and "transit_hours" in ft.columns
    ):

        warehouse = (
            ft
            .groupby(
                "destination_warehouse",
                as_index=False
            )
            .agg(
                avg_transit=("transit_hours", "mean"),
                trips=("transit_hours", "count")
            )
            .sort_values(
                "avg_transit",
                ascending=False
            )
        )

        fig_warehouse = px.bar(
            warehouse,
            x="destination_warehouse",
            y="avg_transit",
            title="Average Transit by Warehouse",
            labels={
                "destination_warehouse": "Warehouse",
                "avg_transit": "Average Transit (hrs)"
            }
        )

        st.plotly_chart(
            fig_warehouse,
            use_container_width=True
        )


# ============================================================
# MANDI HEALTH
# ============================================================

st.markdown(
    '<div class="section-header">'
    '🏪 Mandi Health & Performance'
    '</div>',
    unsafe_allow_html=True
)


if len(mandi_health) > 0:

    health = mandi_health.copy()

    if "health_score" in health.columns:

        health = health.sort_values(
            "health_score",
            ascending=False
        )

        display_cols = []

        for col in [
            "mandi_id",
            "health_score",
            "health_category",
            "price_score",
            "logistics_score"
        ]:

            if col in health.columns:
                display_cols.append(col)

        if display_cols:

            st.dataframe(
                health[display_cols].round(2),
                use_container_width=True,
                hide_index=True
            )

        # Health chart

        top_health = health.head(15)

        fig_health = px.bar(
            top_health,
            x="health_score",
            y="mandi_id",
            orientation="h",
            title="Top Mandi Health Scores",
            labels={
                "health_score": "Health Score",
                "mandi_id": "Mandi"
            }
        )

        st.plotly_chart(
            fig_health,
            use_container_width=True
        )

else:

    st.info(
        "Mandi health score file is not available. "
        "The rest of the dashboard is still usable."
    )


# ============================================================
# WEATHER INTELLIGENCE
# ============================================================

st.markdown(
    '<div class="section-header">'
    '🌦️ Weather Intelligence'
    '</div>',
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# WEATHER KPIs
# ------------------------------------------------------------

w1, w2, w3 = st.columns(3)


if len(fw) > 0:

    avg_temp = (
        fw["temp_c"].mean()
        if "temp_c" in fw.columns
        else np.nan
    )

    total_rain = (
        fw["rainfall_mm"].sum()
        if "rainfall_mm" in fw.columns
        else np.nan
    )

    avg_humidity = (
        fw["humidity_percent"].mean()
        if "humidity_percent" in fw.columns
        else np.nan
    )

else:

    avg_temp = np.nan
    total_rain = np.nan
    avg_humidity = np.nan


with w1:

    st.metric(
        "🌡️ Avg Temperature",
        f"{avg_temp:.1f} °C"
        if pd.notna(avg_temp)
        else "—"
    )


with w2:

    st.metric(
        "🌧️ Total Rainfall",
        f"{total_rain:.1f} mm"
        if pd.notna(total_rain)
        else "—"
    )


with w3:

    st.metric(
        "💧 Avg Humidity",
        f"{avg_humidity:.1f}%"
        if pd.notna(avg_humidity)
        else "—"
    )


# ------------------------------------------------------------
# WEATHER + ARRIVAL MERGE
# ------------------------------------------------------------

if (
    len(fw) > 0
    and len(fa) > 0
    and "date" in fw.columns
    and "date" in fa.columns
    and "rainfall_mm" in fw.columns
    and "arrival_quantity_qtl" in fa.columns
):

    weather_daily = (
        fw
        .groupby("date", as_index=False)
        .agg(
            rainfall_mm=("rainfall_mm", "sum"),
            temp_c=("temp_c", "mean")
        )
    )

    arrivals_daily = (
        fa
        .groupby("date", as_index=False)
        ["arrival_quantity_qtl"]
        .sum()
    )

    weather_impact = weather_daily.merge(
        arrivals_daily,
        on="date",
        how="inner"
    )

    if len(weather_impact) > 1:

        correlation = (
            weather_impact[
                [
                    "rainfall_mm",
                    "arrival_quantity_qtl"
                ]
            ]
            .corr()
            .iloc[0, 1]
        )

    else:

        correlation = np.nan


    wc1, wc2 = st.columns(2)


    with wc1:

        fig_weather = px.scatter(
            weather_impact,
            x="rainfall_mm",
            y="arrival_quantity_qtl",
            trendline="ols",
            title="Rainfall vs Crop Arrivals",
            labels={
                "rainfall_mm": "Rainfall (mm)",
                "arrival_quantity_qtl": "Arrivals (QTL)"
            }
        )

        st.plotly_chart(
            fig_weather,
            use_container_width=True
        )


    with wc2:

        fig_rain = go.Figure()

        fig_rain.add_trace(
            go.Bar(
                x=weather_impact["date"],
                y=weather_impact["rainfall_mm"],
                name="Rainfall (mm)"
            )
        )

        fig_rain.update_layout(
            title="Daily Rainfall",
            xaxis_title="Date",
            yaxis_title="Rainfall (mm)",
            height=420
        )

        st.plotly_chart(
            fig_rain,
            use_container_width=True
        )


    if pd.notna(correlation):

        if correlation < -0.3:

            st.warning(
                f"🌧️ **Weather Signal:** Rainfall and arrivals show a "
                f"negative correlation of {correlation:.2f}. "
                "Higher rainfall is associated with lower arrivals "
                "in the selected period."
            )

        elif correlation > 0.3:

            st.info(
                f"🌦️ **Weather Signal:** Rainfall and arrivals show a "
                f"positive correlation of {correlation:.2f}."
            )

        else:

            st.info(
                f"🌦️ **Weather Signal:** Rainfall and arrivals show "
                f"only a weak linear correlation ({correlation:.2f}) "
                "in the selected period."
            )


else:

    st.info(
        "Weather-arrival analysis requires valid daily weather "
        "and arrival data for the selected filters."
    )


# ============================================================
# BUSINESS ALERTS
# ============================================================

st.markdown(
    '<div class="section-header">'
    '🚨 Business Alerts & Decision Support'
    '</div>',
    unsafe_allow_html=True
)


alerts = []


# Price alert

if pd.notna(avg_msp_gap):

    if avg_msp_gap < -10:

        alerts.append(
            (
                "🔴",
                "HIGH PRICE RISK",
                f"Average market price is {abs(avg_msp_gap):.1f}% "
                "below MSP."
            )
        )

    elif avg_msp_gap < 0:

        alerts.append(
            (
                "🟠",
                "PRICE WATCH",
                f"Average market price is {abs(avg_msp_gap):.1f}% "
                "below MSP."
            )
        )

    else:

        alerts.append(
            (
                "🟢",
                "PRICE POSITIVE",
                f"Average market price is {avg_msp_gap:.1f}% "
                "above MSP."
            )
        )


# Crash alert

if pd.notna(price_crash_rate):

    if price_crash_rate >= 40:

        alerts.append(
            (
                "🔴",
                "WIDESPREAD BELOW-MSP PRESSURE",
                f"{price_crash_rate:.1f}% of valid price observations "
                "are below MSP."
            )
        )

    elif price_crash_rate >= 20:

        alerts.append(
            (
                "🟠",
                "BELOW-MSP PRESSURE",
                f"{price_crash_rate:.1f}% of valid observations "
                "are below MSP."
            )
        )


# Logistics alert

if pd.notna(delay_rate):

    if delay_rate >= 30:

        alerts.append(
            (
                "🔴",
                "LOGISTICS RISK",
                f"{delay_rate:.1f}% of trips exceed the 12-hour "
                "delay threshold."
            )
        )

    elif delay_rate >= 15:

        alerts.append(
            (
                "🟠",
                "LOGISTICS WATCH",
                f"{delay_rate:.1f}% of trips exceed the 12-hour "
                "delay threshold."
            )
        )

    else:

        alerts.append(
            (
                "🟢",
                "LOGISTICS STABLE",
                f"Only {delay_rate:.1f}% of trips exceed "
                "the 12-hour threshold."
            )
        )


# Display alerts

for icon, title, message in alerts:

    if icon == "🔴":

        st.error(
            f"{icon} **{title}** — {message}"
        )

    elif icon == "🟠":

        st.warning(
            f"{icon} **{title}** — {message}"
        )

    else:

        st.success(
            f"{icon} **{title}** — {message}"
        )


# ============================================================
# DATA QUALITY / COVERAGE
# ============================================================

with st.expander("🔍 Data & Model Coverage"):

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        st.metric(
            "Arrival Records",
            f"{len(fa):,}"
        )

    with q2:
        st.metric(
            "Price Records",
            f"{len(fp):,}"
        )

    with q3:
        st.metric(
            "Transport Records",
            f"{len(ft):,}"
        )

    with q4:
        st.metric(
            "Weather Records",
            f"{len(fw):,}"
        )

    st.caption(
        "All dashboard metrics are calculated from the processed "
        "analytics-ready datasets."
    )


# ============================================================
# PROJECT STORY
# ============================================================

st.markdown(
    '<div class="section-header">'
    '🧭 Decision Story'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("""
**How to use this dashboard**

1. **Executive Overview** → understand the current mandi ecosystem.
2. **Price Intelligence** → identify crops and mandis facing below-MSP pressure.
3. **Supply Chain** → identify arrival concentration and logistics bottlenecks.
4. **Weather Intelligence** → investigate whether weather conditions are associated with arrival changes.
5. **Business Alerts** → prioritize the areas requiring management attention.

The dashboard is designed to move from **What is happening → Where is the problem → What may be driving it → What deserves attention**.
""")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "TransOrg AgentIQ Datathon • Track 3: AgriTech • "
    "Mandi-to-Market Supply Chain Optimizer"
)

st.caption(
    "Interactive analytics dashboard built with Streamlit + Plotly"
)





# ============================================================
# 🤖 AGENTIC GRAPH AI
# ============================================================

import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots


st.markdown("---")

st.markdown(
    """
    <div class="section-header">
    🤖 Ask Agri Intelligence
    </div>
    """,
    unsafe_allow_html=True
)

st.write(
    "Ask a business question in natural language and the agent "
    "will select the appropriate chart and generate a business insight."
)


# ============================================================
# LOAD CLEAN DATA FOR AGENT
# ============================================================

@st.cache_data
def load_agent_data():

    base = Path(__file__).resolve().parents[1]
    processed = base / "data" / "processed"

    arrivals_path = processed / "arrivals_fact.csv"
    prices_path = processed / "prices_fact.csv"
    mandi_path = processed / "mandi_dim.csv"
    weather_path = processed / "weather_daily.csv"
    transport_path = processed / "transport_fact.csv"

    arrivals_agent = pd.read_csv(arrivals_path)
    prices_agent = pd.read_csv(prices_path)
    mandi_agent = pd.read_csv(mandi_path)

    # Optional files
    if weather_path.exists():
        weather_agent = pd.read_csv(weather_path)
    else:
        weather_agent = pd.DataFrame()

    if transport_path.exists():
        transport_agent = pd.read_csv(transport_path)
    else:
        transport_agent = pd.DataFrame()

    # --------------------------------------------------------
    # Standardize dates
    # --------------------------------------------------------

    for df in [
        arrivals_agent,
        prices_agent,
        weather_agent,
        transport_agent
    ]:

        if "date" in df.columns:

            df["date"] = pd.to_datetime(
                df["date"],
                errors="coerce"
            ).dt.normalize()

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    for col in [
        "arrival_quantity_qtl"
    ]:

        if col in arrivals_agent.columns:

            arrivals_agent[col] = pd.to_numeric(
                arrivals_agent[col],
                errors="coerce"
            )

    for col in [
        "modal_price",
        "msp",
        "min_price",
        "max_price"
    ]:

        if col in prices_agent.columns:

            prices_agent[col] = pd.to_numeric(
                prices_agent[col],
                errors="coerce"
            )

    if "rainfall_mm" in weather_agent.columns:

        weather_agent["rainfall_mm"] = pd.to_numeric(
            weather_agent["rainfall_mm"],
            errors="coerce"
        )

    if "temp_c" in weather_agent.columns:

        weather_agent["temp_c"] = pd.to_numeric(
            weather_agent["temp_c"],
            errors="coerce"
        )

    if "transit_hours" in transport_agent.columns:

        transport_agent["transit_hours"] = pd.to_numeric(
            transport_agent["transit_hours"],
            errors="coerce"
        )

    return (
        arrivals_agent,
        prices_agent,
        mandi_agent,
        weather_agent,
        transport_agent
    )


(
    AG_ARRIVALS,
    AG_PRICES,
    AG_MANDI,
    AG_WEATHER,
    AG_TRANSPORT
) = load_agent_data()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value):

    if pd.isna(value):
        return ""

    value = str(value).lower().strip()

    value = re.sub(
        r"[^a-z0-9\u0900-\u097f\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def find_crop_agent(question):

    q = normalize_text(question)

    crop_aliases = {

        "Wheat": [
            "wheat",
            "gehun",
            "gehu",
            "गेहूं"
        ],

        "Rice": [
            "rice",
            "paddy",
            "chawal",
            "धान",
            "चावल"
        ],

        "Maize": [
            "maize",
            "corn",
            "makka",
            "makki",
            "मक्का"
        ],

        "Cotton": [
            "cotton",
            "kapas",
            "narma",
            "कपास"
        ],

        "Mustard": [
            "mustard",
            "sarson",
            "sarso",
            "सरसों"
        ],

        "Sugarcane": [
            "sugarcane",
            "ganna",
            "ganne",
            "गन्ना"
        ]
    }

    for canonical, aliases in crop_aliases.items():

        for alias in aliases:

            if normalize_text(alias) in q:

                return canonical

    # Check actual dataset crops
    if "crop_name" in AG_ARRIVALS.columns:

        for crop in AG_ARRIVALS["crop_name"].dropna().unique():

            if normalize_text(crop) in q:

                return crop

    return None


# ============================================================
# FIND MANDI
# ============================================================

def find_mandi_agent(question):

    q = normalize_text(question)

    if (
        "mandi_name" not in AG_MANDI.columns
        or "mandi_id" not in AG_MANDI.columns
    ):

        return None

    mandi_data = AG_MANDI[
        ["mandi_id", "mandi_name"]
    ].dropna(
        subset=["mandi_id"]
    ).drop_duplicates()

    # Exact / partial mandi name
    for _, row in mandi_data.iterrows():

        name = normalize_text(
            row["mandi_name"]
        )

        if not name:
            continue

        if name in q:

            return str(row["mandi_id"])

    # Word-level matching
    for _, row in mandi_data.iterrows():

        name = normalize_text(
            row["mandi_name"]
        )

        words = name.split()

        for word in words:

            if len(word) >= 4 and word in q:

                return str(row["mandi_id"])

    return None


# ============================================================
# DATE RANGE
# ============================================================

def get_date_range_agent(question, dataframe):

    if "date" not in dataframe.columns:

        return None, None

    dates = dataframe["date"].dropna()

    if len(dates) == 0:

        return None, None

    latest = dates.max()

    q = normalize_text(question)

    if (
        "last 7 days" in q
        or "past 7 days" in q
    ):

        return (
            latest - pd.Timedelta(days=6),
            latest
        )

    if (
        "last 30 days" in q
        or "past 30 days" in q
    ):

        return (
            latest - pd.Timedelta(days=29),
            latest
        )

    if (
        "last 90 days" in q
        or "past 90 days" in q
    ):

        return (
            latest - pd.Timedelta(days=89),
            latest
        )

    return None, None


# ============================================================
# FILTER DATA
# ============================================================

def filter_agent_data(
    dataframe,
    question
):

    df = dataframe.copy()

    crop = find_crop_agent(question)

    mandi_id = find_mandi_agent(question)

    start_date, end_date = get_date_range_agent(
        question,
        df
    )

    # Crop filter
    if (
        crop is not None
        and "crop_name" in df.columns
    ):

        target = normalize_text(crop)

        df = df[
            df["crop_name"]
            .fillna("")
            .astype(str)
            .apply(normalize_text)
            .apply(
                lambda x:
                x == target
                or target in x
                or x in target
            )
        ]

    # Mandi filter
    if (
        mandi_id is not None
        and "mandi_id" in df.columns
    ):

        df = df[
            df["mandi_id"]
            .astype(str)
            == str(mandi_id)
        ]

    # Date filter
    if (
        start_date is not None
        and end_date is not None
        and "date" in df.columns
    ):

        df = df[
            (df["date"] >= start_date)
            &
            (df["date"] <= end_date)
        ]

    return df


# ============================================================
# AGENT
# ============================================================

def run_agri_agent(question):

    q = normalize_text(question)

    crop = find_crop_agent(question)

    mandi_id = find_mandi_agent(question)

    start_date, end_date = get_date_range_agent(
        question,
        AG_ARRIVALS
    )

    # ========================================================
    # 1. DAILY ARRIVAL + MSP
    # ========================================================

    if (
        "arrival" in q
        and (
            "msp" in q
            or "price" in q
            or "market" in q
        )
    ):

        arrivals = filter_agent_data(
            AG_ARRIVALS,
            question
        )

        prices = filter_agent_data(
            AG_PRICES,
            question
        )

        if len(arrivals) == 0:

            return {
                "success": False,
                "message": (
                    "No arrival records were found for "
                    "the requested crop/mandi/date."
                )
            }

        if len(prices) == 0:

            return {
                "success": False,
                "message": (
                    "Arrival data was found, but matching "
                    "price/MSP records were not found."
                )
            }

        arrival_daily = (
            arrivals
            .groupby("date", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
        )

        price_daily = (
            prices
            .groupby("date", as_index=False)
            .agg(
                modal_price=("modal_price", "mean"),
                msp=("msp", "mean")
            )
        )

        merged = arrival_daily.merge(
            price_daily,
            on="date",
            how="inner"
        ).sort_values("date")

        if len(merged) == 0:

            return {
                "success": False,
                "message": (
                    "Arrival and price data exist, but "
                    "there are no matching dates."
                )
            }

        crop_text = (
            crop
            if crop
            else "All crops"
        )

        mandi_text = "selected mandi"

        if mandi_id is not None:

            matches = AG_MANDI[
                AG_MANDI["mandi_id"].astype(str)
                == str(mandi_id)
            ]

            if len(matches) > 0:

                mandi_text = str(
                    matches.iloc[0]["mandi_name"]
                )

        result = {
            "success": True,
            "type": "arrival_msp",
            "title": (
                f"{crop_text} Daily Arrivals vs MSP"
            ),
            "data": merged,
            "summary": (
                f"{crop_text} recorded "
                f"{merged['arrival_quantity_qtl'].sum():,.0f} QTL "
                f"of arrivals in {mandi_text}. "
                f"The average modal price was "
                f"₹{merged['modal_price'].mean():,.0f} "
                f"against an average MSP of "
                f"₹{merged['msp'].mean():,.0f}."
            )
        }

        return result


    # ========================================================
    # 2. MARKET PRICE VS MSP
    # ========================================================

    if (
        "price" in q
        and "msp" in q
    ):

        prices = filter_agent_data(
            AG_PRICES,
            question
        )

        if len(prices) == 0:

            return {
                "success": False,
                "message": (
                    "No price/MSP records were found "
                    "for that request."
                )
            }

        daily = (
            prices
            .groupby("date", as_index=False)
            .agg(
                modal_price=("modal_price", "mean"),
                msp=("msp", "mean")
            )
            .sort_values("date")
        )

        if len(daily) == 0:

            return {
                "success": False,
                "message": (
                    "No valid dated price records "
                    "were available."
                )
            }

        avg_price = daily["modal_price"].mean()

        avg_msp = daily["msp"].mean()

        gap = (
            (avg_price - avg_msp)
            / avg_msp
            * 100
            if avg_msp != 0
            else 0
        )

        crop_text = (
            crop
            if crop
            else "selected crop"
        )

        return {
            "success": True,
            "type": "price_msp",
            "title": (
                f"{crop_text} Market Price vs MSP"
            ),
            "data": daily,
            "summary": (
                f"For {crop_text}, the average modal price "
                f"was ₹{avg_price:,.0f}, compared with "
                f"an average MSP of ₹{avg_msp:,.0f}. "
                f"The average MSP gap was {gap:+.1f}%."
            )
        }


    # ========================================================
    # 3. ARRIVAL TREND
    # ========================================================

    if (
        "arrival" in q
        or "supply" in q
    ):

        arrivals = filter_agent_data(
            AG_ARRIVALS,
            question
        )

        if len(arrivals) == 0:

            return {
                "success": False,
                "message": (
                    "No arrival records were found."
                )
            }

        daily = (
            arrivals
            .groupby("date", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
            .sort_values("date")
        )

        return {
            "success": True,
            "type": "arrival",
            "title": "Daily Crop Arrival Trend",
            "data": daily,
            "summary": (
                f"Total arrivals during the selected "
                f"period were "
                f"{daily['arrival_quantity_qtl'].sum():,.0f} QTL."
            )
        }


    # ========================================================
    # 4. CROP COMPARISON
    # ========================================================

    if (
        "crop" in q
        and (
            "compare" in q
            or "by crop" in q
            or "highest" in q
            or "top" in q
            or "distribution" in q
        )
    ):

        crop_data = (
            AG_ARRIVALS
            .groupby("crop_name", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
            .sort_values(
                "arrival_quantity_qtl",
                ascending=False
            )
        )

        return {
            "success": True,
            "type": "bar",
            "title": "Arrival Volume by Crop",
            "data": crop_data,
            "summary": (
                f"{crop_data.iloc[0]['crop_name']} "
                f"has the highest total arrival volume "
                f"at "
                f"{crop_data.iloc[0]['arrival_quantity_qtl']:,.0f} QTL."
            )
        }


    # ========================================================
    # 5. MANDI COMPARISON
    # ========================================================

    if (
        "mandi" in q
        and (
            "compare" in q
            or "highest" in q
            or "top" in q
            or "by mandi" in q
        )
    ):

        mandi_data = (
            AG_ARRIVALS
            .groupby("mandi_id", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
            .sort_values(
                "arrival_quantity_qtl",
                ascending=False
            )
            .head(15)
        )

        mandi_lookup = AG_MANDI[
            ["mandi_id", "mandi_name"]
        ].drop_duplicates()

        mandi_data = mandi_data.merge(
            mandi_lookup,
            on="mandi_id",
            how="left"
        )

        mandi_data["display_name"] = (
            mandi_data["mandi_name"]
            .fillna(
                mandi_data["mandi_id"]
            )
        )

        return {
            "success": True,
            "type": "bar",
            "title": "Top Mandis by Arrival Volume",
            "data": mandi_data,
            "summary": (
                f"{mandi_data.iloc[0]['display_name']} "
                f"has the highest arrival volume."
            )
        }


    # ========================================================
    # 6. WEATHER VS ARRIVALS
    # ========================================================

    if (
        "rainfall" in q
        or "weather" in q
        or "temperature" in q
    ):

        if len(AG_WEATHER) == 0:

            return {
                "success": False,
                "message": "Weather data is not available."
            }

        arrivals_daily = (
            AG_ARRIVALS
            .groupby("date", as_index=False)
            ["arrival_quantity_qtl"]
            .sum()
        )

        weather_daily = (
            AG_WEATHER
            .groupby("date", as_index=False)
            .agg(
                rainfall_mm=("rainfall_mm", "sum"),
                temp_c=("temp_c", "mean")
            )
        )

        merged = arrivals_daily.merge(
            weather_daily,
            on="date",
            how="inner"
        )

        if len(merged) < 2:

            return {
                "success": False,
                "message": (
                    "Not enough overlapping weather "
                    "and arrival data."
                )
            }

        corr = merged[
            [
                "rainfall_mm",
                "arrival_quantity_qtl"
            ]
        ].corr().iloc[0, 1]

        return {
            "success": True,
            "type": "weather",
            "title": "Rainfall vs Crop Arrivals",
            "data": merged,
            "summary": (
                f"The correlation between rainfall and "
                f"arrivals is {corr:.2f}. "
                "This indicates the strength and direction "
                "of the observed relationship."
            )
        }


    # ========================================================
    # 7. LOGISTICS
    # ========================================================

    if (
        "transit" in q
        or "logistics" in q
        or "warehouse" in q
        or "delay" in q
    ):

        if len(AG_TRANSPORT) == 0:

            return {
                "success": False,
                "message": "Transport data is not available."
            }

        if "destination_warehouse" not in AG_TRANSPORT.columns:

            return {
                "success": False,
                "message": (
                    "Warehouse information is not available."
                )
            }

        logistics = (
            AG_TRANSPORT
            .dropna(
                subset=["transit_hours"]
            )
            .groupby(
                "destination_warehouse",
                as_index=False
            )
            .agg(
                avg_transit_hours=(
                    "transit_hours",
                    "mean"
                )
            )
            .sort_values(
                "avg_transit_hours",
                ascending=False
            )
        )

        return {
            "success": True,
            "type": "bar",
            "title": "Average Transit Time by Warehouse",
            "data": logistics,
            "summary": (
                f"{logistics.iloc[0]['destination_warehouse']} "
                f"has the highest average transit time at "
                f"{logistics.iloc[0]['avg_transit_hours']:.1f} hours."
            )
        }


    # ========================================================
    # NO MATCH
    # ========================================================

    return {
        "success": False,
        "message": (
            "I could not understand that business question."
        )
    }


# ============================================================
# QUESTION INPUT
# ============================================================

agent_question = st.text_input(
    "💬 Ask Agri Intelligence",
    placeholder=(
        "Example: Plot the daily arrival trend of Wheat "
        "in Amritsar mandi vs MSP for the last 30 days"
    )
)


st.caption(
    "Try: "
    "Daily Wheat arrivals • "
    "Market price vs MSP • "
    "Crop comparison • "
    "Rainfall vs arrivals • "
    "Mandi comparison"
)


# ============================================================
# RUN AGENT
# ============================================================

if agent_question.strip():

    with st.spinner(
        "🧠 Agri Intelligence is analyzing your question..."
    ):

        result = run_agri_agent(
            agent_question
        )


    if not result["success"]:

        st.error(
            result["message"]
        )

    else:

        # ====================================================
        # AGENT DECISION
        # ====================================================

        chart_type = result["type"]

        if chart_type == "arrival_msp":

            decision = "Line chart + dual-axis comparison"

        elif chart_type == "price_msp":

            decision = "Line chart"

        elif chart_type == "weather":

            decision = "Scatter chart"

        elif chart_type in ["bar", "mandi"]:

            decision = "Bar chart"

        else:

            decision = "Line chart"

        st.success(
            f"🤖 Agent selected: **{decision}**"
        )


        # ====================================================
        # ARRIVAL + MSP
        # ====================================================

        if chart_type == "arrival_msp":

            df = result["data"]

            fig = make_subplots(
                specs=[
                    [
                        {
                            "secondary_y": True
                        }
                    ]
                ]
            )

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["arrival_quantity_qtl"],
                    mode="lines+markers",
                    name="Arrivals (QTL)"
                ),
                secondary_y=False
            )

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["modal_price"],
                    mode="lines+markers",
                    name="Modal Price (₹)"
                ),
                secondary_y=True
            )

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["msp"],
                    mode="lines",
                    name="MSP (₹)",
                    line=dict(
                        dash="dash"
                    )
                ),
                secondary_y=True
            )

            fig.update_layout(
                title=result["title"],
                height=520,
                hovermode="x unified"
            )

            fig.update_xaxes(
                title_text="Date"
            )

            fig.update_yaxes(
                title_text="Arrivals (QTL)",
                secondary_y=False
            )

            fig.update_yaxes(
                title_text="Price (₹)",
                secondary_y=True
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ====================================================
        # PRICE VS MSP
        # ====================================================

        elif chart_type == "price_msp":

            df = result["data"]

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["modal_price"],
                    mode="lines+markers",
                    name="Modal Price"
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["msp"],
                    mode="lines",
                    name="MSP",
                    line=dict(
                        dash="dash"
                    )
                )
            )

            fig.update_layout(
                title=result["title"],
                xaxis_title="Date",
                yaxis_title="Price (₹)",
                height=500,
                hovermode="x unified"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ====================================================
        # ARRIVAL TREND
        # ====================================================

        elif chart_type == "arrival":

            df = result["data"]

            fig = px.line(
                df,
                x="date",
                y="arrival_quantity_qtl",
                markers=True,
                title=result["title"]
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Arrivals (QTL)",
                height=500
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ====================================================
        # WEATHER
        # ====================================================

        elif chart_type == "weather":

            df = result["data"]

            fig = px.scatter(
                df,
                x="rainfall_mm",
                y="arrival_quantity_qtl",
                trendline="ols",
                title=result["title"],
                labels={
                    "rainfall_mm": "Rainfall (mm)",
                    "arrival_quantity_qtl": "Arrivals (QTL)"
                }
            )

            fig.update_layout(
                height=500
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ====================================================
        # BAR CHARTS
        # ====================================================

        elif chart_type == "bar":

            df = result["data"]

            x_col = df.columns[0]

            y_col = df.columns[1]

            fig = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=result["title"]
            )

            fig.update_layout(
                height=500
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        # ====================================================
        # BUSINESS INSIGHT
        # ====================================================

        st.subheader(
            "💡 Agent Insight"
        )

        st.info(
            result["summary"]
        )


        # ====================================================
        # DATA USED
        # ====================================================

        with st.expander(
            "📋 View data used by the agent"
        ):

            st.dataframe(
                result["data"],
                use_container_width=True,
                hide_index=True
            )