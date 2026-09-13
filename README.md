# 🌾 Agri Mandi-to-Market Supply Chain Optimizer

> **TransOrg AgentIQ Datathon 2026 --- Track 3: AgriTech**

An end-to-end data engineering, analytics, dashboard, and agentic AI
solution that turns messy mandi data into clean, query-ready datasets
and actionable supply-chain insights.

**Live Dashboard:**
https://agri-mandi-complete-with-profiling-znmfmqknclx6nqktujfrqq.streamlit.app/
**GitHub:**
https://github.com/Nandeeshwarreddy2006/agri-mandi-complete-with-profiling

------------------------------------------------------------------------

## 1. Executive Summary

Agricultural mandi data can contain inconsistent crop names, mixed
units, missing values, duplicate records, inconsistent identifiers,
different weather formats, and invalid logistics values. These issues
make direct analysis unreliable.

This project builds a reproducible pipeline that:

**Profiles → Cleans → Standardizes → Validates → Models → Analyzes →
Visualizes → Answers**

The solution combines five messy source datasets into a governed
analytical layer, calculates supply, price, weather, and logistics
metrics, presents the results through an interactive Streamlit
dashboard, and provides an Agentic Graph AI interface for
natural-language business questions.

The goal is simple: **turn messy mandi data into trusted information
that helps decision-makers understand supply, price pressure, weather
conditions, and logistics performance.**

------------------------------------------------------------------------

## 2. Business Problem

Mandi stakeholders need to answer questions such as:

-   How much of each crop is arriving?
-   Which crops or mandis have unusually high or low supply?
-   How are market prices performing against MSP?
-   Which crops are under price pressure?
-   Is rainfall associated with changes in arrivals?
-   Which warehouses or routes have higher transit times?
-   Can a decision-maker ask these questions without manually building
    queries and charts?

The original data is not analysis-ready because the same business
concept can appear in different formats.

The solution therefore focuses on **data quality first, analytics
second, and decision support third**.

------------------------------------------------------------------------

## 3. Solution Architecture

``` text
Raw Messy Datasets
        ↓
01. Data Profiling
        ↓
02. Data Cleaning & Standardization
        ↓
03. Data Validation
        ↓
04. Analytical Data Model
        ↓
05. KPIs & Analytics
        ↓
06. Business Insights
        ↓
Interactive Streamlit Dashboard
        ↓
Agentic Graph AI
        ↓
Natural Language → Intent → Entities → Filters
→ SQL Query Plan → DataFrame → Chart Selection
→ Plotly Visualization → Insight Summary
```

### Architecture Layers

  -----------------------------------------------------------------------
  Layer                               Purpose
  ----------------------------------- -----------------------------------
  Data Rescue                         Identify and fix messy, incomplete,
                                      duplicate and inconsistent data

  Analytics Layer                     Build clean fact/dimension datasets
                                      and business metrics

  Executive Dashboard                 Provide interactive filters, KPIs,
                                      charts, alerts and price
                                      intelligence

  Agentic Graph AI                    Convert natural-language questions
                                      into analytical results and
                                      visualizations
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 4. Dataset

The project uses the organizer-provided Track 3 AgriTech dataset.

  -------------------------------------------------------------------------------------
  Dataset                            Purpose                                Raw Records
  ---------------------------------- --------------------- ----------------------------
  `track3_mandi_arrivals.csv`        Daily crop arrivals                         25,750

  `track3_price_and_msp.json`        Market prices and MSP                       12,000

  `track3_weather_sensors.xlsx`      Weather sensor                              15,000
                                     observations          

  `track3_transport_logistics.csv`   Transport and transit                       10,400
                                     information           

  `track3_mandi_master.csv`          Mandi/district master                           60
                                     data                  
  -------------------------------------------------------------------------------------

### Analytical outputs

-   `arrivals_fact.csv`
-   `prices_fact.csv`
-   `mandi_dim.csv`
-   `transport_fact.csv`
-   `weather_daily.csv`

------------------------------------------------------------------------

## 5. Data Quality Issues

### Crop names

Examples included `WHEAT`, `Wheat`, `Gehun`, `GEHUN`, `Kanak`, and `गेहूं`.
These were standardized into six canonical crops:

**Wheat, Rice, Maize, Cotton, Mustard, Sugarcane**

### Quantity

KG, KGS, Q, Qtl, Quintal, MT, T, and Tonnes were converted to **quintals
(Qtl)**.

### Prices

Currency-formatted strings such as `₹7,570.17`, `Rs. 7,299`, and
`INR 2,183` were converted to numeric values.

### Weather

UTC/IST timestamps, Celsius/Fahrenheit temperatures, mm/inches rainfall,
and missing sensor values were standardized. Weather was aggregated to
daily level.

### Transport

KM/miles were standardized to KM, invalid transit values were handled,
and duplicate/missing fields were addressed.

### Mandi master

Duplicate records, inconsistent IDs, and missing district/state/type
fields were handled.

------------------------------------------------------------------------

## 6. Cleaning Methodology

The pipeline follows a reproducible sequence:

1.  **Profile** --- inspect structure, missing values, duplicates and
    messy values.
2.  **Clean** --- remove/handle duplicate records and invalid values.
3.  **Standardize** --- canonical crop names, mandi IDs, units, dates
    and numeric fields.
4.  **Convert units** --- quantities to Qtl, distances to KM, Fahrenheit
    to Celsius, inches to mm.
5.  **Aggregate** --- create daily weather analytics.
6.  **Validate** --- check schemas, types, row counts, standardization
    and relationships.
7.  **Save** --- produce query-ready analytical CSVs.

Detailed evidence is documented in `CLEANING_EVIDENCE.md`.

------------------------------------------------------------------------

## 7. Data Model

The analytical layer uses a simple fact/dimension structure:

``` text
                 mandi_dim
                    |
        +-----------+-----------+
        |           |           |
   arrivals_fact prices_fact transport_fact
                    |
               weather_daily
                    |
              Analytics Layer
```

Relationships are primarily based on standardized `mandi_id` and
analytical `date`.

------------------------------------------------------------------------

## 8. KPI Definitions

  ------------------------------------------------------------------------
  KPI                                 Definition
  ----------------------------------- ------------------------------------
  Total Arrivals                      Sum of standardized arrival quantity
                                      in Qtl

  Average Arrival                     Mean arrival quantity per analytical
                                      record

  Average Market Price                Mean modal market price

  Average MSP                         Mean MSP

  Price Gap                           Market Price − MSP

  Price Gap %                         `(Market Price − MSP) / MSP × 100`

  Average Transit                     Mean valid transit time in hours

  Average Rainfall                    Mean daily rainfall in mm

  Rainfall--Arrival Correlation       Correlation between daily rainfall
                                      and daily arrivals
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 9. Business Insights

The analytics layer supports four main decision areas:

-   **Supply:** identify crops and mandis with unusually high or low
    arrival volumes.
-   **Price:** detect market prices below or above MSP and quantify the
    gap.
-   **Weather:** compare rainfall patterns with changes in daily
    arrivals.
-   **Logistics:** identify warehouses/routes with higher transit times.

Decision flow:

**DATA → PATTERN → INSIGHT → ACTION**

------------------------------------------------------------------------

## 10. Interactive Dashboard

The Streamlit dashboard provides:

-   Crop filter
-   Mandi filter
-   Time Period filter: All Time, 7 Days, 30 Days, 90 Days, Custom
-   KPI cards
-   Daily arrival trends
-   Crop-wise arrival distribution
-   Market Price vs MSP
-   Mandi performance
-   Logistics analysis
-   Weather analysis
-   Business Insights & Alerts
-   Price Intelligence
-   Interactive Plotly charts

**Live Dashboard:**
https://agri-mandi-complete-with-profiling-znmfmqknclx6nqktujfrqq.streamlit.app/

------------------------------------------------------------------------

## 11. Agentic Graph AI

Users can ask questions such as:

-   `Which crop has the highest total arrivals?`
-   `Show market price vs MSP for Wheat`
-   `Show the daily arrival trend of Wheat`
-   `Which mandis have the highest arrivals?`

The agent pipeline is:

``` text
Natural Language
      ↓
Intent Extraction
      ↓
Entity Extraction
      ↓
Filter Detection
      ↓
SQL Query Plan
      ↓
DataFrame
      ↓
Chart Selection
      ↓
Plotly Visualization
      ↓
Business Insight Summary
```

Supported analytical intents include Price vs MSP, Daily Arrival Trend,
Top Crops, Top Mandis, Weather Impact, and Logistics Performance.

The SQL displayed by the agent is an explainable analytical query plan;
the deployed implementation executes the equivalent operations on the
cleaned pandas data.

------------------------------------------------------------------------

## 12. Validation

Validation is performed after cleaning and before analytics.

Checks include:

-   Row-count reconciliation
-   Duplicate checks
-   Required-column checks
-   Data-type checks
-   Date parsing
-   Crop standardization
-   Mandi-ID standardization
-   Quantity conversion
-   Numeric price validation
-   Invalid transit handling
-   Output-file checks
-   Cross-dataset relationship checks

Notebook order:

``` text
01_data_profiling.ipynb
02_data_cleaning.ipynb
03_data_validation.ipynb
04_data_model.ipynb
05_analytics.ipynb
06_insights.ipynb
```

------------------------------------------------------------------------

## 13. Data Dictionary

A dedicated `DATA_DICTIONARY.md` documents the fields in:

-   `arrivals_fact.csv`
-   `prices_fact.csv`
-   `mandi_dim.csv`
-   `transport_fact.csv`
-   `weather_daily.csv`

Core fields include crop, mandi, date, arrival quantity, modal price,
MSP, transit time, distance, temperature, rainfall and humidity.

------------------------------------------------------------------------

## 14. Installation

Requirements:

-   Python 3.10+
-   Jupyter Notebook/JupyterLab
-   Streamlit

Install dependencies:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 15. How to Run

### Clone

``` bash
git clone https://github.com/Nandeeshwarreddy2006/agri-mandi-complete-with-profiling.git
cd agri-mandi-complete-with-profiling
```

### Install

``` bash
pip install -r requirements.txt
```

### Run notebooks in order

``` text
01_data_profiling.ipynb
02_data_cleaning.ipynb
03_data_validation.ipynb
04_data_model.ipynb
05_analytics.ipynb
06_insights.ipynb
```

### Launch dashboard

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

## 16. Cleaning Evidence

  Dataset                 Raw Rows   Cleaned / Output Rows
  --------------------- ---------- -----------------------
  Mandi Master                  60                      57
  Mandi Arrivals            25,750                  25,750
  Price & MSP               12,000                  12,000
  Weather Sensors           15,000       151 daily records
  Transport Logistics       10,400                  10,400

The weather reduction is intentional: sensor-level observations are
aggregated into daily analytical records.

See `CLEANING_EVIDENCE.md` for the detailed evidence.

------------------------------------------------------------------------

## 17. Limitations

1.  The project uses the organizer-provided datathon dataset rather than
    a live production feed.
2.  Weather-to-mandi mapping depends on the relationships available in
    the provided data.
3.  Rainfall-arrival correlation indicates association, not causation.
4.  Dashboard signals are decision-support indicators, not guaranteed
    forecasts.
5.  Missing source values cannot always be recovered without additional
    authoritative data.
6.  The Agentic AI currently supports a defined set of analytical
    intents rather than unrestricted questions.
7.  The displayed SQL is an explainable query plan; equivalent
    operations are executed on pandas dataframes.

------------------------------------------------------------------------

## 18. Future Improvements

-   Real-time mandi data ingestion
-   DuckDB or production SQL analytics layer
-   Automated data-quality monitoring
-   Price and arrival forecasting
-   Supply and price anomaly detection
-   Improved geographic weather mapping
-   Route-level logistics optimization
-   More Agentic AI business intents
-   Multilingual natural-language queries
-   Role-based views for farmers, traders and policymakers
-   Scheduled pipeline execution
-   Data and model lineage tracking

------------------------------------------------------------------------

## 19. Technology Stack

**Python · Pandas · NumPy · Plotly · Streamlit · Jupyter · GitHub ·
Agentic AI**

------------------------------------------------------------------------

## 20. Repository Structure

``` text
agri-mandi-complete-with-profiling/
├── 01_data_profiling.ipynb
├── 02_data_cleaning.ipynb
├── 03_data_validation.ipynb
├── 04_data_model.ipynb
├── 05_analytics.ipynb
├── 06_insights.ipynb
├── app.py
├── agent.py
├── arrivals_fact.csv
├── prices_fact.csv
├── mandi_dim.csv
├── transport_fact.csv
├── weather_daily.csv
├── DATA_DICTIONARY.md
├── CLEANING_EVIDENCE.md
├── README.md
└── requirements.txt
```

------------------------------------------------------------------------

## 21. Deliverables

### Data Rescue

Messy source data → standardized, validated analytical datasets.

### Analytics

Fact/dimension model → KPIs → business insights.

### Executive Dashboard

Interactive filters → KPIs → charts → alerts → price intelligence.

### Agentic Graph AI

Natural language → analytical intent → query plan → chart → business
insight.

------------------------------------------------------------------------

## 22. Submission Links

**GitHub:**\
https://github.com/Nandeeshwarreddy2006/agri-mandi-complete-with-profiling

**Live Dashboard:**\
https://agri-mandi-complete-with-profiling-znmfmqknclx6nqktujfrqq.streamlit.app/

------------------------------------------------------------------------

## 23. Closing

**Clean Data. Smarter Mandis. Stronger Decisions. 🌾**

Built for **TransOrg AgentIQ Datathon 2026 --- Track 3: AgriTech**.
