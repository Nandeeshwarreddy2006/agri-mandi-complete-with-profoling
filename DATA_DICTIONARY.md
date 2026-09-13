# Data Dictionary

## Project
**Agri Mandi-to-Market Supply Chain Optimizer**

This data dictionary describes the cleaned and analytics-ready datasets used in the project.

---

## 1. arrivals_fact.csv

This table contains cleaned mandi crop arrival records.

| Column | Description | Data Type |
|---|---|---|
| arrival_id | Unique identifier for an arrival record | String |
| date | Date of crop arrival | Date |
| mandi_id | Standardized identifier of the mandi | String |
| crop_name | Canonical crop name after standardization | String |
| variety | Crop variety | String |
| arrival_quantity | Original numeric arrival quantity | Numeric |
| unit | Standardized quantity unit | String |
| farmer_count | Number of farmers associated with the arrival | Numeric |
| quantity_to_qtl_factor | Conversion factor used to convert the original unit into quintals | Numeric |
| arrival_quantity_qtl | Arrival quantity converted into quintals | Numeric |

### Quantity Standardization

All arrival quantities are converted to **quintals (Qtl)**.

- 1 Quintal = 100 KG
- 1 Tonne = 10 Quintals
- KG values are converted using 0.01 Qtl per KG

---

## 2. prices_fact.csv

This table contains cleaned crop market prices and Minimum Support Price (MSP) information.

| Column | Description | Data Type |
|---|---|---|
| record_id | Unique identifier for a price record | String |
| date | Date of the price record | Date |
| mandi_id | Standardized mandi identifier | String |
| crop_name | Canonical crop name | String |
| district | District associated with the mandi | String |
| min_price | Minimum reported market price | Numeric |
| max_price | Maximum reported market price | Numeric |
| modal_price | Modal/representative market price | Numeric |
| msp | Minimum Support Price for the crop | Numeric |

### Price Standardization

Currency symbols and text formats such as:

- ₹
- Rs.
- Rs
- INR
- Commas in numeric values

are cleaned before converting prices into numeric values.

---

## 3. mandi_dim.csv

This is the cleaned mandi master/dimension table.

| Column | Description | Data Type |
|---|---|---|
| mandi_id | Standardized unique mandi identifier | String |
| mandi_name | Name of the mandi | String |
| district | District where the mandi is located | String |
| state | State where the mandi is located | String |
| mandi_type | Type/category of mandi | String |

This table acts as the master reference for connecting mandi-level datasets.

---

## 4. transport_fact.csv

This table contains cleaned transportation and logistics records.

| Column | Description | Data Type |
|---|---|---|
| trip_id | Unique identifier for a transport trip | String |
| date | Transport/trip date | Date |
| source | Source location of the shipment | String |
| destination_warehouse | Destination warehouse | String |
| transit_hours | Transit duration in hours | Numeric |
| distance | Original numeric travel distance | Numeric |
| distance_unit | Unit of recorded distance | String |
| vehicle_no | Standardized vehicle registration number | String |
| driver_id | Identifier of the driver | String |
| distance_km | Distance standardized to kilometres | Numeric |

### Distance Standardization

All transport distances are converted to kilometres.

- Kilometres are retained as KM
- Miles are converted to KM

Invalid negative transit-time values are treated as invalid/missing during cleaning.

---

## 5. weather_daily.csv

This table contains weather information aggregated at the daily level.

| Column | Description | Data Type |
|---|---|---|
| date | Calendar date | Date |
| temp_c | Average temperature in Celsius | Numeric |
| rainfall_mm | Total daily rainfall in millimetres | Numeric |
| humidity_percent | Average daily relative humidity percentage | Numeric |

### Weather Standardization

Weather measurements are standardized before analysis:

- Fahrenheit → Celsius
- Inches → millimetres
- UTC timestamps → Indian Standard Time (IST)
- Weather observations are aggregated by date

---

# Key Relationships

The datasets are connected through common business keys and dates.

```text
mandi_dim
   │
   ├── mandi_id ──> arrivals_fact
   │
   ├── mandi_id ──> prices_fact
   │
   └── mandi_id ──> transport_fact

weather_daily
   │
   └── date ──> daily arrival / analytics layer
