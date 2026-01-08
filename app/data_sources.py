from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import BASE_URL, DATA_TYPE, TYPE_PARAM, YEAR_PARAM


def _fetch_page(year: int) -> BeautifulSoup:
    params = {TYPE_PARAM: DATA_TYPE, YEAR_PARAM: year}
    headers = {"User-Agent": UserAgent().random}
    response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


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

    return sorted(set(years)), href, reference_year


def _download_year_data(year: int, link_template: str, reference_year: int) -> pd.DataFrame:
    url = link_template.replace(str(reference_year), str(year))
    headers = {"User-Agent": UserAgent().random}
    response = requests.get(url, headers=headers, timeout=60)
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
