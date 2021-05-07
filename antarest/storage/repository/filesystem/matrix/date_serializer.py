from abc import ABC, abstractmethod
from typing import Tuple

import pandas as pd  # type: ignore


class IDateMatrixSerializer(ABC):
    _MONTHS = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUNE": "06",
        "JULY": "07",
        "AUG": "08",
        "SEPT": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12",
    }

    @abstractmethod
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        pass


class HourlyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["Unnamed: 2", "Unnamed: 3", "Unnamed: 4"]]
        date.columns = ["day", "month", "hour"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date = (
            date["hour"] + " " + date["day"] + "/" + date["month"].astype(str)
        )

        # Extract right part with data
        node = df.columns[0]
        body = df.drop(
            [node, "hourly", "Unnamed: 2", "Unnamed: 3", "Unnamed: 4"], axis=1
        )

        return pd.Index(date), body


class DailyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["Unnamed: 2", "Unnamed: 3"]]
        date.columns = ["day", "month"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date = date["day"] + "/" + date["month"].astype(str)

        # Extract right part with data
        node = df.columns[0]
        body = df.drop([node, "daily", "Unnamed: 2", "Unnamed: 3"], axis=1)

        return pd.Index(date), body


class WeeklyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["weekly"]]

        # Extract right part with data
        node = df.columns[0]
        body = df.drop([node, "weekly"], axis=1)

        return pd.Index(range(date.size)), body


class MonthlyMatrixSerializer(IDateMatrixSerializer):
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["Unnamed: 2"]]
        date.columns = ["month"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)

        # Extract right part with data
        node = df.columns[0]
        body = df.drop([node, "monthly", "Unnamed: 2"], axis=1)

        return pd.Index(date["month"]), body


class AnnualMatrixSerializer(IDateMatrixSerializer):
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.loc[2:, ["annual"]]

        # Extract right part with data
        node = df.columns[0]
        body = df.drop([node, "annual"], axis=1)

        return pd.Index(date["annual"]), body


class FactoryDateSerializer:
    @staticmethod
    def create(freq: str) -> IDateMatrixSerializer:
        if freq == "hourly":
            return HourlyMatrixSerializer()
        if freq == "daily":
            return DailyMatrixSerializer()
        if freq == "weekly":
            return WeeklyMatrixSerializer()
        if freq == "monthly":
            return MonthlyMatrixSerializer()
        if freq == "annual":
            return AnnualMatrixSerializer()

        raise NotImplementedError(
            f"Any date serializer compatible with freq={freq}"
        )
