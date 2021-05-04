from abc import ABC, abstractmethod
from typing import Tuple

import pandas as pd


class IDateMatrixSerializer(ABC):
    _MONTHS = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUNE": 6,
        "JULY": 7,
        "AUG": 8,
        "SEPT": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12,
    }

    @abstractmethod
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
        pass


class DailyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DatetimeIndex, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["Unnamed: 2", "Unnamed: 3"]]
        date.columns = ["day", "month"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date["year"] = 2020
        date = pd.DatetimeIndex(pd.to_datetime(date))

        # Extract right part with data
        node = df.columns[0]
        body = df.drop([node, "daily", "Unnamed: 2", "Unnamed: 3"], axis=1)

        return date, body
