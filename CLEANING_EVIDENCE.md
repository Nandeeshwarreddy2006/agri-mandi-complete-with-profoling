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

## 2. Raw → Cleaned Dataset Evidence

The following table shows the transformation from the organizer-provided raw datasets to the analytics-ready datasets used in the project.

| Dataset | Raw Rows | Cleaned / Output Rows | Main Data Quality Issues |
|---|---:|---:|---|
| Mandi Master | 60 | 57 | Duplicate records, missing district/state/type, inconsistent IDs |
| Mandi Arrivals | 25,750 | 25,750 | Duplicate IDs, messy crop names, mixed units, missing farmer counts |
| Price & MSP | 12,000 | 12,000 | String-formatted prices, missing price/MSP values, inconsistent crop/mandi information |
| Weather Sensors | 15,000 | 151 daily records | Missing timestamps, mixed Celsius/Fahrenheit, mixed rainfall units, missing humidity |
| Transport Logistics | 10,400 | 10,400 | Duplicate records, duplicate trip IDs, missing fields, mixed KM/miles, invalid transit values |

### Important Notes

- **Mandi Master:** 60 raw rows were reduced to 57 records after duplicate handling.
- **Mandi Arrivals:** The analytics-ready arrivals table contains 25,750 records. Cleaning focused on standardization, unit conversion, date normalization and data-quality handling.
- **Price & MSP:** The analytics-ready price table contains 12,000 records after numeric and format standardization.
- **Weather:** 15,000 sensor-level observations were transformed into **151 daily records** through date-based aggregation. Therefore, the weather output row count is intentionally not a one-to-one comparison with the raw dataset.
- **Transport:** The analytics-ready transport table contains 10,400 records after cleaning and standardization.

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
