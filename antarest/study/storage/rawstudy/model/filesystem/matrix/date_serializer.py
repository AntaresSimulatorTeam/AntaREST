import re
from abc import ABC, abstractmethod
from typing import Tuple, List

import pandas as pd  # type: ignore
from pandas import DataFrame


class IDateMatrixSerializer(ABC):
    """
    Abstract class to handle date index reading and writing for many time frequency.
    Used by OutputSeriesMatrix
    """

    _MONTHS = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12",
    }
    _R_MONTHS = {v: k for k, v in _MONTHS.items()}

    def __init__(self, area: str):
        self.area = area

    @abstractmethod
    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        """
        Extract date from raw columns inside matrix file
        Args:
            df: raw matrix from file content

        Returns: (date index, other matrix part)

        """
        raise NotImplementedError()

    @abstractmethod
    def build_date(self, index: pd.Index) -> pd.DataFrame:
        """
        Format in antares style date index
        Args:
            index: date index

        Returns: raw matrix date waith antares style ready to be save on disk

        """
        raise NotImplementedError()


def rename_unnamed(df: DataFrame) -> DataFrame:
    unnamed_cols: List[str] = []
    for i in range(0, df.columns.nlevels):
        unnamed_cols += [
            name
            for name in df.columns.get_level_values(i).values
            if "Unnamed:" in name
        ]
    df.rename(columns={name: "" for name in unnamed_cols}, inplace=True)
    return df


class HourlyMatrixSerializer(IDateMatrixSerializer):
    """
    Class implementation for hourly index
    """

    def build_date(self, index: pd.Index) -> pd.DataFrame:
        def _map(row: str) -> Tuple[str, int, str, str, str]:
            m, d, h = re.split("[\s/]", row)
            return "", 1, d.strip("0"), IDateMatrixSerializer._R_MONTHS[m], h

        items = index.map(_map).tolist()
        matrix = pd.DataFrame(items)
        matrix[1] = matrix[1].cumsum()

        headers = pd.DataFrame(
            [
                [self.area.upper(), "hourly", "", "", ""],
                ["", "", "", "", ""],
                ["", "index", "day", "month", "hour"],
            ]
        )

        return pd.concat([headers, matrix], axis=0)

    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.iloc[
            :,
            2:5,
        ]
        date.columns = ["day", "month", "hour"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date = (
            date["month"].astype(str)
            + "/"
            + date["day"].astype(str).str.zfill(2)
            + " "
            + date["hour"]
        )

        # Extract right part with data
        to_remove = df.columns[0:5]
        body = df.drop(
            to_remove,
            axis=1,
        )

        return pd.Index(date), body


class DailyMatrixSerializer(IDateMatrixSerializer):
    """
    Class implementation for daily index
    """

    def build_date(self, index: pd.Index) -> pd.DataFrame:
        def _map(row: str) -> Tuple[str, int, str, str]:
            m, d = row.split("/")
            return "", 1, d.strip("0"), IDateMatrixSerializer._R_MONTHS[m]

        items = index.map(_map).tolist()
        matrix = pd.DataFrame(items)
        matrix[1] = matrix[1].cumsum()

        headers = pd.DataFrame(
            [
                [self.area.upper(), "daily", "", ""],
                ["", "", "", ""],
                ["", "index", "day", "month"],
            ]
        )

        return pd.concat([headers, matrix], axis=0)

    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.iloc[:, 2:4]
        date.columns = ["day", "month"]
        date["month"] = date["month"].map(IDateMatrixSerializer._MONTHS)
        date = (
            date["month"].astype(str)
            + "/"
            + date["day"].astype(str).str.zfill(2)
        )

        # Extract right part with data
        to_remove = df.columns[0:4]
        body = df.drop(
            to_remove,
            axis=1,
        )

        return pd.Index(date), body


class WeeklyMatrixSerializer(IDateMatrixSerializer):
    """
    Class implementation for weekly index
    """

    def build_date(self, index: pd.Index) -> pd.DataFrame:
        matrix = pd.DataFrame({0: [""] * index.size, 1: index.values})

        headers = pd.DataFrame(
            [
                [self.area.upper(), "weekly"],
                ["", ""],
                ["", "week"],
            ]
        )

        return pd.concat([headers, matrix], axis=0)

    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.iloc[:, 1:2]
        date.columns = ["weekly"]

        # Extract right part with data
        to_remove = df.columns[0:2]
        body = df.drop(to_remove, axis=1)

        return pd.Index(date["weekly"]), body


class MonthlyMatrixSerializer(IDateMatrixSerializer):
    """
    Class implementation for monthly index
    """

    def build_date(self, index: pd.Index) -> pd.DataFrame:
        matrix = pd.DataFrame(
            {
                0: [""] * index.size,
                1: range(1, index.size + 1),
                2: index.map(IDateMatrixSerializer._R_MONTHS),
            }
        )

        headers = pd.DataFrame(
            [
                [self.area.upper(), "monthly", ""],
                ["", "", ""],
                ["", "index", "month"],
            ]
        )

        return pd.concat([headers, matrix], axis=0)

    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.iloc[:, 2:3]
        date.columns = ["month"]
        date["month"] = date.loc[:, "month"].map(IDateMatrixSerializer._MONTHS)

        # Extract right part with data
        to_remove = df.columns[0:3]
        body = df.drop(to_remove, axis=1)

        return pd.Index(date["month"]), body


class AnnualMatrixSerializer(IDateMatrixSerializer):
    """
    Class implementation for annual index
    """

    def build_date(self, index: pd.Index) -> pd.DataFrame:
        return pd.DataFrame(
            [
                [self.area.upper(), "annual"],
                ["", ""],
                ["", ""],
                ["", "Annual"],
            ]
        )

    def extract_date(self, df: pd.DataFrame) -> Tuple[pd.Index, pd.DataFrame]:
        # Extract left part with date
        date = df.iloc[:, 1:2]
        date.columns = ["annual"]

        # Extract right part with data
        to_remove = df.columns[0:2]
        body = df.drop(to_remove, axis=1)

        return pd.Index(date["annual"]), body


class FactoryDateSerializer:
    """
    Factory to choice correct DateMatrixSerializer according antares time frequency
    """

    @staticmethod
    def create(freq: str, area: str) -> IDateMatrixSerializer:
        if freq == "hourly":
            return HourlyMatrixSerializer(area)
        if freq == "daily":
            return DailyMatrixSerializer(area)
        if freq == "weekly":
            return WeeklyMatrixSerializer(area)
        if freq == "monthly":
            return MonthlyMatrixSerializer(area)
        if freq == "annual":
            return AnnualMatrixSerializer(area)

        raise NotImplementedError(
            f"Any date serializer compatible with freq={freq}"
        )
