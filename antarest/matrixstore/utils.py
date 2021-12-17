import csv
from pathlib import Path
from typing import List

from antarest.matrixstore.model import MatrixData, MatrixDTO


def parse_tsv_matrix(file_data: bytes) -> List[List[MatrixData]]:
    data: List[List[MatrixData]] = []
    str_file = str(file_data, "UTF-8")
    reader = csv.reader(str_file.split("\n"), delimiter="\t")

    for row in reader:
        if row:
            data.append([MatrixData(elm) for elm in row])

    return data


def write_tsv_matrix_to_file(data: MatrixDTO, filepath: str):
    with open(filepath, "w+", encoding="UTF8") as f:
        writer = csv.writer(f, delimiter="\t")
        for row in data.data:
            writer.writerow(row)


def write_tsv_matrix(data: MatrixDTO, output_tmp_dir: str):
    name = f"matrix-{data.id}.txt"
    filepath = f"{output_tmp_dir}/{name}"
    write_tsv_matrix_to_file(data, filepath)
