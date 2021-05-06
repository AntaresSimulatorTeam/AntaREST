from abc import ABC, abstractmethod
from typing import Tuple

import pandas as pd  # type: ignore


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
    def extract_date(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DatetimeIndex, pd.DataFrame]:
        pass


class HourlyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["Unnamed: 2", "Unnamed: 3", "Unnamed: 4"]]
        date.columns = ["day", "month", "hour"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date = date["hour"] + " " + date["day"] + "/" + date["month"]

        # Extract right part with data
        node = df.columns[0]
        body = df.drop(
            [node, "hourly", "Unnamed: 2", "Unnamed: 3", "Unnamed 4"], axis=1
        )

        return date, body


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


class MonthlyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DatetimeIndex, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["Unnamed: 2"]]
        date.columns = ["month"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date["year"] = 2020
        date["day"] = 1
        date = pd.DatetimeIndex(pd.to_datetime(date))

        # Extract right part with data
        node = df.columns[0]
        body = df.drop([node, "monthly", "Unnamed: 2"], axis=1)

        return date, body


class FactoryDateSerializer:
    @staticmethod
    def create(freq: str) -> IDateMatrixSerializer:
        if freq == "daily":
            return DailyMatrixSerializer()
        if freq == "monthly":
            return MonthlyMatrixSerializer()
        raise NotImplementedError(
            f"Any date serializer compatible with freq={freq}"
        )
