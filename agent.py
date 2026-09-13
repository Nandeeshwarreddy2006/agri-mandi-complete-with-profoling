import pandas as pd
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
P=BASE/"data"/"processed"/"analytics"

daily=pd.read_csv(P/"daily_arrivals.csv",parse_dates=["date"])
crop=pd.read_csv(P/"crop_kpi.csv")
mandi=pd.read_csv(P/"mandi_kpi.csv")

def answer(question):
    q=question.lower()
    if "arrival" in q and "trend" in q:
        return daily.tail(30)[["date","arrival_quantity_qtl"]]
    if "crop" in q:
        return crop.sort_values("total_arrivals_qtl",ascending=False)
    if "mandi" in q:
        return mandi.sort_values("total_arrivals_qtl",ascending=False).head(10)
    return "Ask about arrival trends, crops, or mandis."

if __name__=="__main__":
    print(answer(input("Ask a question: ")))
