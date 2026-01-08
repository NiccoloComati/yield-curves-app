from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import BASE_URL, DATA_TYPE, MIN_AVAILABLE_YEAR, TYPE_PARAM, USER_AGENT, YEAR_PARAM


def _fetch_page(year: int) -> BeautifulSoup:
    params = {TYPE_PARAM: DATA_TYPE, YEAR_PARAM: year}
    response = requests.get(
        BASE_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=30
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_available_years(reference_year: int) -> tuple[list[int], str, int]:
    soup = _fetch_page(reference_year)

    select = soup.find("select", {"data-drupal-selector": "edit-field-tdr-date-value"})
    years: list[int] = []
    if select:
        for option in select.find_all("option"):
            value = option.get("value") or option.text
            if value and value.isdigit():
                years.append(int(value))

    link_wrapper = soup.find("div", class_="csv-feed views-data-export-feed")
    link_tag = link_wrapper.find("a") if link_wrapper else None
    if not link_tag or not link_tag.get("href"):
        raise ValueError("CSV export link not found on the Treasury site.")

    href = link_tag.get("href")
    if href.startswith("/"):
        href = f"https://home.treasury.gov{href}"

    if not years:
        years = _probe_available_years(href, reference_year)

    return sorted(set(years)), href, reference_year


def _probe_available_years(link_template: str, reference_year: int) -> list[int]:
    years: list[int] = []
    for year in range(MIN_AVAILABLE_YEAR, reference_year + 1):
        if _year_has_data(link_template, reference_year, year):
            years.append(year)
    return years


def _year_has_data(link_template: str, reference_year: int, year: int) -> bool:
    url = link_template.replace(str(reference_year), str(year))
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=20)
        if response.status_code != 200:
            return False
        chunk = next(response.iter_content(chunk_size=256), b"")
        return b"Date" in chunk
    except Exception:
        return False


def _download_year_data(year: int, link_template: str, reference_year: int) -> pd.DataFrame:
    url = link_template.replace(str(reference_year), str(year))
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
    df.columns = df.columns.str.strip('"')
    return df


def load_yield_data(
    years: Iterable[int], link_template: str, reference_year: int
) -> pd.DataFrame:
    year_list = list(years)
    if not year_list:
        return pd.DataFrame()

    with ThreadPoolExecutor(max_workers=min(8, len(year_list))) as executor:
        dfs = list(
            executor.map(
                lambda y: _download_year_data(y, link_template, reference_year),
                year_list,
            )
        )
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")
    return df_all
