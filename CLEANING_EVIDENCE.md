# Cleaning Evidence

## Agri Mandi-to-Market Supply Chain Optimizer

This document provides evidence of the data rescue and cleaning performed on the organizer-provided AgriTech datasets.

The objective was to transform messy, inconsistent source data into structured, analytics-ready datasets for the dashboard and Agentic AI layer.

---

## 1. Raw Data Profiling

The raw datasets were profiled before cleaning to identify:

- Duplicate records
- Duplicate identifiers
- Missing values
- Inconsistent crop names
- Inconsistent mandi identifiers
- Mixed measurement units
- String-based numeric values
- Mixed date formats
- Mixed weather units
- Time-zone inconsistencies
- Invalid transport values

The profiling was performed in:

`01_data_profiling.ipynb`

---

## 2. Raw Dataset Evidence

| Dataset | Raw Rows | Main Data Quality Issues |
|---|---:|---|
| Mandi Master | 60 | Duplicate records, missing district/state/type, inconsistent IDs |
| Mandi Arrivals | 25,750 | 750 exact duplicates, duplicate IDs, messy crop names, mixed units, missing farmer counts |
| Price & MSP | 12,000 | String-formatted prices, missing price/MSP values, inconsistent crop/mandi information |
| Weather Sensors | 15,000 | Missing timestamps, mixed Celsius/Fahrenheit, mixed rainfall units, missing humidity |
| Transport Logistics | 10,400 | 400 exact duplicates, duplicate trip IDs, missing fields, mixed KM/miles, invalid transit values |

---

# 3. Cleaning Operations

## A. Mandi Arrivals

### Problems Identified

- Duplicate rows
- Duplicate arrival IDs
- Crop names represented in English, Hindi and Punjabi
- Different spellings and capitalization
- Quantity recorded in KG, Qtl and Tonnes
- Missing farmer counts
- Inconsistent dates

### Cleaning Performed

- Removed exact duplicate records
- Standardized mandi identifiers
- Standardized crop names into canonical crop categories
- Converted quantities into numeric values
- Standardized units
- Converted all quantities into quintals
- Standardized date values
- Preserved missing values where reliable replacement was not possible

### Quantity Conversion

```text
1 KG       = 0.01 Quintal
1 Quintal  = 1 Quintal
1 Tonne    = 10 Quintals
