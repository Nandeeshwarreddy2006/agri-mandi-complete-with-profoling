# Agri Mandi-to-Market Supply Chain Optimizer

## Notebook order
1. 01_data_profiling.ipynb — existing profiling notebook
2. 02_data_cleaning.ipynb
3. 03_data_validation.ipynb
4. 04_data_model.ipynb
5. 05_analytics.ipynb
6. 06_insights.ipynb
7. dashboard/app.py
8. agent/agent.py

## Important
In every notebook, change:
`BASE = Path(r"C:\CHANGE\THIS\TO\YOUR\PROJECT")`
to your project folder.

Run notebooks in order because later notebooks use the CSV files produced by earlier notebooks.

## Dashboard
From the project folder:
`pip install -r requirements.txt`
`streamlit run dashboard/app.py`
