from typing import Dict

import pandas as pd
import yfinance as yf
import os

# intialize the years, pull will be run by year just in case
start_dates = [str(i) + "-01-01" for i in range(2007, 2022)]
end_dates = [str(i) + "-01-01" for i in range(2007, 2022)]

# add odd ones on the beginning and end
start_dates = ["2006-05-16"] + start_dates
end_dates = end_dates + ["2021-02-18"]

# dict of the name for the output file and then query string for Yahoo Finance
tickers = {
    "SP500": "^GSPC",
    "AX200": "^AXJO",
    "AUDUSD": "AUDUSD=X",
    "AUDCNY": "AUDCNY=X",
    "AUDJPN": "AUDJPY=X",
    "AUDEUR": "AUDEUR=X",
}


def pull_data(
    tickers: Dict[str, str], start_date: str, end_date: str
) -> Dict[str, pd.DataFrame]:
    """Call to YahooFinance based on the provided tickers

    Args:
        tickers (Dict[str, str]): ticker filename and API ticker symbol
        start_date (str): date for pull range to start
        end_date (str): date for pull range to end

    Raises:
        ValueError: When ticker symbol or dates are wrong

    Returns:
        Dict[str, pd.DataFrame]: Dictionary of raw data as dataframe objects
        with the ticker filename as the key
    """

    if type(tickers) != type(dict()):
        raise TypeError("Tickers not passed as dictionary")

    if type(start_date) != type(str()) and type(end_date) != type(str()):
        raise TypeError("Dates need to be strings")

    data = {}

    try:
        for k, v in tickers.items():

            raw = yf.download(v, start=start_date, end=end_date)

            data[k] = raw
    except ValueError as ve:
        print("Check that the dictionary and dates are correct for {v}")

    return data


def write_data(data: Dict[str, pd.DataFrame], start_date: str, end_date: str) -> None:
    """Writes data as csv to local storge folder 'data'
     naming based on ticker and dates

    Args:
        data (Dict[str, pd.DataFrame]): Dictionary of raw data as dataframe objects
        with the ticker filename as the key
        start_date (str): date for pull range to start
        end_date (str): date for pull range to end

    Raises:
        KeyError: When file fails to write
    """

    if type(tickers) != type(dict()):
        raise TypeError("Data not passed as dictionary")

    if type(start_date) != type(str()) and type(end_date) != type(str()):
        raise TypeError("Dates need to be strings")

    for k, v in data.items():

        try:
            path = f"./data/{k}/"
            os.makedirs(path, exist_ok=True)
            file_name = path + k + "_" + start_date + "_" + end_date + ".csv"
            df = v.reset_index()
            df.to_csv(file_name, index=False)

            print(f"Wrote {file_name}")

        except KeyError as ke:
            print(f"Failed to write file for {k}")


#  wrapper function
def run(tickers, start_date, end_date):
    data = pull_data(tickers, start_date, end_date)
    write_data(data, start_date, end_date)


if __name__ == "__main__":

    for dates in [start_dates, end_dates]:
        assert len(dates) == 16, "Need 16 years to run"

        assert all(
            s for s in dates if type(s) == "str" and len(s.split("-")) == 3
        ), "Should be YYYY-MM-DD string format"

    for i in range(len(start_dates)):
        print("Pulling data from:", start_dates[i], "to", end_dates[i])
        run(tickers, start_dates[i], end_dates[i])
