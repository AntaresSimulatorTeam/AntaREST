import csv
from typing import List

from antarest.matrixstore.model import MatrixData


def parse_tsv_matrix(file_data: bytes) -> List[List[MatrixData]]:
    data: List[List[MatrixData]] = []
    str_file = str(file_data, "UTF-8")
    reader = csv.reader(str_file.split("\n"), delimiter="\t")

    for row in reader:
        if row:
            data.append([MatrixData(elm) for elm in row])

    return data
