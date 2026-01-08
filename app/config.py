from datetime import date

BASE_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView"
DATA_TYPE = "daily_treasury_yield_curve"
YEAR_PARAM = "field_tdr_date_value"
TYPE_PARAM = "type"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) StreamlitApp/1.0"

MIN_AVAILABLE_YEAR = 1990

DEFAULT_START = date(2006, 6, 1)
DEFAULT_END = date(2008, 12, 31)

MATURITY_MAPPING = {
    "1 Mo": 0.5,
    "2 Mo": 1,
    "3 Mo": 1.5,
    "4 Mo": 2,
    "6 Mo": 2.8,
    "1 Yr": 4,
    "2 Yr": 6,
    "3 Yr": 8,
    "5 Yr": 11,
    "7 Yr": 14,
    "10 Yr": 17,
    "20 Yr": 21,
    "30 Yr": 25,
}
