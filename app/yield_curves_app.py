from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from charts import plot_yield_curves
from config import DEFAULT_END, DEFAULT_START
from data_sources import get_available_years, load_yield_data


st.set_page_config(page_title="US Treasury Yield Curves", layout="wide")
st.title("US Treasury Yield Curve Visualizer")
st.caption("Explore daily yield curves from the US Treasury.")


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_years_and_template(reference_year: int) -> tuple[list[int], str, int]:
    return get_available_years(reference_year)


@st.cache_data(show_spinner=True, ttl=60 * 60 * 24)
def get_yield_data(years: list[int], link_template: str, reference_year: int) -> pd.DataFrame:
    return load_yield_data(years, link_template, reference_year)


reference_year = dt.date.today().year
try:
    available_years, link_template, template_year = get_years_and_template(reference_year)
except Exception as exc:
    st.error(f"Failed to load metadata from Treasury: {exc}")
    st.stop()

if not available_years:
    st.error("No available years returned by Treasury.")
    st.stop()

min_date = dt.date(min(available_years), 1, 1)
max_date = dt.date(max(available_years), 12, 31)

start_value = max(min(DEFAULT_START, max_date), min_date)
end_value = max(min(DEFAULT_END, max_date), min_date)
if start_value > end_value:
    start_value, end_value = min_date, max_date

start_date = st.date_input("Start Date", value=start_value, min_value=min_date, max_value=max_date)
end_date = st.date_input("End Date", value=end_value, min_value=min_date, max_value=max_date)

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

selected_years = [year for year in available_years if start_date.year <= year <= end_date.year]
if not selected_years:
    st.warning("No data available for the selected date range.")
    st.stop()

with st.spinner("Downloading and processing yield curve data..."):
    df_all = get_yield_data(selected_years, link_template, template_year)

df_filtered = df_all[
    (df_all["Date"] >= pd.to_datetime(start_date))
    & (df_all["Date"] <= pd.to_datetime(end_date))
].copy()

if not df_filtered.empty:
    st.plotly_chart(plot_yield_curves(df_filtered), use_container_width=True)
else:
    st.warning("No data for the selected period.")
