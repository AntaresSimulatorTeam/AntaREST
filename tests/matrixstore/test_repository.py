# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import datetime
import shutil
import typing as t
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from numpy import typing as npt
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.config import InternalMatrixFormat
from antarest.login.model import Group, Password, User
from antarest.login.repository import GroupRepository, UserRepository
from antarest.matrixstore.model import Matrix, MatrixDataSet, MatrixDataSetRelation
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository

ArrayData = t.Union[t.List[t.List[float]], npt.NDArray[np.float64]]


class TestMatrixRepository:
    def test_db_lifecycle(self, db_session: Session) -> None:
        with db_session:
            repo = MatrixRepository(db_session)
            m = Matrix(id="hello", created_at=datetime.datetime.now())
            repo.save(m)
            assert m.id
            assert m == repo.get(m.id)
            assert repo.exists(m.id)
            repo.delete(m.id)
            assert repo.get(m.id) is None

    def test_bucket_lifecycle(self, tmp_path: Path) -> None:
        repo = MatrixContentRepository(tmp_path, InternalMatrixFormat.TSV)

        a: ArrayData = [[1, 2], [3, 4]]
        b: ArrayData = [[5, 6], [7, 8]]

        matrix_content_a = pd.DataFrame(data=a, index=[0, 1], columns=[0, 1])
        matrix_content_b = pd.DataFrame(data=b, index=[0, 1], columns=[0, 1])

        aid = repo.save(a)
        assert aid == repo.save(a)

        bid = repo.save(b)
        assert aid != bid

        assert matrix_content_a.equals(repo.get(aid))
        assert matrix_content_b.equals(repo.get(bid))

        repo.delete(aid)
        with pytest.raises(FileNotFoundError):
            repo.get(aid)

    def test_dataset(self, db_session: Session) -> None:
        with db_session:
            repo = MatrixRepository(session=db_session)

            user_repo = UserRepository(session=db_session)
            user = user_repo.save(User(name="foo", password=Password("bar")))

            group_repo = GroupRepository(session=db_session)
            group = group_repo.save(Group(name="group"))

            dataset_repo = MatrixDataSetRepository(session=db_session)

            m1 = Matrix(id="hello", created_at=datetime.datetime.now())
            repo.save(m1)
            m2 = Matrix(id="world", created_at=datetime.datetime.now())
            repo.save(m2)

            dataset = MatrixDataSet(
                name="some name",
                public=True,
                owner_id=user.id,
                groups=[group],
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )

            matrix_relation = MatrixDataSetRelation(name="m1")
            matrix_relation.matrix_id = "hello"
            dataset.matrices.append(matrix_relation)
            matrix_relation = MatrixDataSetRelation(name="m2")
            matrix_relation.matrix_id = "world"
            dataset.matrices.append(matrix_relation)

            dataset = dataset_repo.save(dataset)
            dataset_query_result = dataset_repo.get(dataset.id)
            assert dataset_query_result is not None
            assert dataset_query_result.name == "some name"
            assert len(dataset_query_result.matrices) == 2

            dataset_update = MatrixDataSet(
                id=dataset.id,
                name="some name change",
                public=False,
                updated_at=datetime.datetime.now(),
            )
            dataset_repo.save(dataset_update)
            dataset_query_result = dataset_repo.get(dataset.id)
            assert dataset_query_result is not None
            assert dataset_query_result.name == "some name change"
            assert dataset_query_result.owner_id == user.id

    def test_datastore_query(self, db_session: Session) -> None:
        # sourcery skip: extract-duplicate-method
        with db_session:
            user_repo = UserRepository(session=db_session)
            user1 = user_repo.save(User(name="foo", password=Password("bar")))
            user2 = user_repo.save(User(name="hello", password=Password("world")))

            repo = MatrixRepository(session=db_session)
            m1 = Matrix(id="hello", created_at=datetime.datetime.now())
            repo.save(m1)
            m2 = Matrix(id="world", created_at=datetime.datetime.now())
            repo.save(m2)

            dataset_repo = MatrixDataSetRepository(session=db_session)

            dataset = MatrixDataSet(
                name="some name",
                public=True,
                owner_id=user1.id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            matrix_relation = MatrixDataSetRelation(name="m1")
            matrix_relation.matrix_id = "hello"
            dataset.matrices.append(matrix_relation)
            matrix_relation = MatrixDataSetRelation(name="m2")
            matrix_relation.matrix_id = "world"
            dataset.matrices.append(matrix_relation)
            dataset_repo.save(dataset)

            dataset = MatrixDataSet(
                name="some name 2",
                public=False,
                owner_id=user2.id,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            matrix_relation = MatrixDataSetRelation(name="m1")
            matrix_relation.matrix_id = "hello"
            dataset.matrices.append(matrix_relation)
            dataset_repo.save(dataset)

            res = dataset_repo.query("name 2")
            assert len(res) == 1
            assert len(res[0].matrices) == 1
            assert res[0].matrices[0].name == "m1"
            assert res[0].matrices[0].matrix.id == m1.id
            assert len(dataset_repo.query("name 2")) == 1
            assert len(dataset_repo.query("name")) == 2
            assert len(dataset_repo.query(None, user1.id)) == 1
            assert len(dataset_repo.query("name 2", user1.id)) == 0

            dataset_repo.delete(dataset.id)
            assert len(dataset_repo.query("name 2")) == 0
            assert repo.get(m1.id) is not None
            assert (
                # fmt: off
                db_session.query(MatrixDataSetRelation).filter(MatrixDataSetRelation.dataset_id == dataset.id).count()
                # fmt: on
                == 0
            )


@contextmanager
def matrix_repository(temp_path: Path, matrix_format: InternalMatrixFormat):
    try:
        yield MatrixContentRepository(bucket_dir=temp_path.joinpath("matrix-store"), format=matrix_format)
    finally:
        shutil.rmtree(temp_path / "matrix-store")


class TestMatrixContentRepository:
    @pytest.mark.parametrize("matrix_format", ["tsv", "hdf", "parquet", "feather"])
    def test_save(self, tmp_path: str, matrix_format: str) -> None:
        """
        Saves the content of a matrix as a file in the directory and returns its SHA256 hash.
        """
        matrix_format = InternalMatrixFormat(matrix_format)
        with matrix_repository(Path(tmp_path), matrix_format) as matrix_content_repo:
            bucket_dir = matrix_content_repo.bucket_dir

            # when the data is saved in the repo
            data: ArrayData
            data = [[1, 2, 3], [4, 5, 6]]
            matrix_hash = matrix_content_repo.save(data)
            # then a file is created in the repo directory
            matrix_file = bucket_dir.joinpath(f"{matrix_hash}.{matrix_format}")
            assert matrix_file.exists()
            array = matrix_format.load_matrix(matrix_file)
            assert array.tolist() == data
            modif_time = matrix_file.stat().st_mtime

            # when the data is saved again with same float values
            data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
            matrix_content_repo.save(data)
            # then no new file is created
            matrix_files = list(bucket_dir.glob(f"*.{matrix_format}"))
            assert matrix_files == [matrix_file]
            assert matrix_file.stat().st_mtime == modif_time, "date changed!"

            # when the data is saved again as NumPy array
            data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
            matrix_content_repo.save(data)
            # then no new file is created
            matrix_files = list(bucket_dir.glob(f"*.{matrix_format}"))
            assert matrix_files == [matrix_file]
            assert matrix_file.stat().st_mtime == modif_time, "date changed!"

            # when other data is saved with different values
            other_data = [[9.0, 2.0, 3.0], [10.0, 20.0, 30.0]]
            other_matrix_hash = matrix_content_repo.save(other_data)
            # then a new file is created
            matrix_files = list(bucket_dir.glob(f"*.{matrix_format}"))
            other_matrix_file = bucket_dir.joinpath(f"{other_matrix_hash}.{matrix_format}")
            assert set(matrix_files) == {matrix_file, other_matrix_file}

            # Test with an empty matrix
            empty_array: ArrayData = []
            matrix_hash = matrix_content_repo.save(empty_array)
            matrix_file = bucket_dir.joinpath(f"{matrix_hash}.{matrix_format}")
            retrieved_matrix = matrix_content_repo.get(matrix_hash)

            assert not matrix_file.read_bytes()
            assert retrieved_matrix.data == [[]]

            # Test with an empty 2D array
            empty_2d_array: ArrayData = [[]]
            matrix_hash = matrix_content_repo.save(empty_2d_array)
            matrix_file = bucket_dir.joinpath(f"{matrix_hash}.{matrix_format}")
            retrieved_matrix = matrix_content_repo.get(matrix_hash)

            assert not matrix_file.read_bytes()
            assert retrieved_matrix.data == [[]]

    @pytest.mark.parametrize("matrix_format", ["tsv", "hdf", "parquet", "feather"])
    def test_get_exists_and_delete(self, tmp_path: str, matrix_format: str) -> None:
        """
        Retrieves the content of a matrix with a given SHA256 hash.
        """
        matrix_format = InternalMatrixFormat(matrix_format)
        with matrix_repository(Path(tmp_path), matrix_format) as matrix_content_repo:
            # when the data is saved in the repo
            data: ArrayData = [[1, 2, 3], [4, 5, 6]]
            matrix_hash = matrix_content_repo.save(data)
            # then the saved matrix object exists
            assert matrix_content_repo.exists(matrix_hash)
            # and it can be retrieved
            content = matrix_content_repo.get(matrix_hash)
            assert content.index == list(range(len(data)))
            assert content.columns == list(range(len(data[0])))
            assert content.data == data

            # we can delete the data that was previously saved
            matrix_content_repo.delete(matrix_hash)
            # and the file doesn't exist anymore
            matrix_files = list(matrix_content_repo.bucket_dir.glob(f"*.{matrix_format}"))
            assert not matrix_files

            # when the data is missing (wrong SHA256)
            # then the saved matrix object doesn't exist and a `FileNotFoundError` is raised
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            assert not matrix_content_repo.exists(missing_hash)
            with pytest.raises(FileNotFoundError):
                matrix_content_repo.get(missing_hash)
            # it cannot be deleted
            with pytest.raises(FileNotFoundError):
                matrix_content_repo.delete(missing_hash)

    @pytest.mark.parametrize("matrix_format", ["tsv", "hdf", "parquet", "feather"])
    def test_mixed_formats(self, tmp_path: str, matrix_format: str) -> None:
        """
        Tests that mixed formats are well handled.
        """
        saved_format = InternalMatrixFormat(matrix_format)
        for repository_format in InternalMatrixFormat:
            if repository_format != saved_format:
                # MatrixContentRepository differs from the one where file were created.
                # This situation will occur if we change the default format inside the app config.
                with matrix_repository(Path(tmp_path), repository_format) as matrix_content_repo:
                    data: ArrayData = [[1, 2, 3], [4, 5, 6]]
                    df = pd.DataFrame(data)
                    associated_hash = "d73f023a3f852bf2e5c6d836cd36cd930d0091dcba7f778161c707e1c58222b0"
                    matrix_path = matrix_content_repo.bucket_dir.joinpath(f"{associated_hash}.{saved_format}")
                    saved_format.save_matrix(df, matrix_path)

                    # asserts the saved matrix object exists
                    assert matrix_content_repo.exists(associated_hash)
                    # and it can be retrieved
                    content = matrix_content_repo.get(associated_hash)
                    assert content.index == list(range(len(data)))
                    assert content.columns == list(range(len(data[0])))
                    assert content.data == data

                    # we can delete the data that was previously saved
                    matrix_content_repo.delete(associated_hash)
                    # and the file doesn't exist anymore
                    matrix_files = list(matrix_content_repo.bucket_dir.glob("*"))
                    assert not matrix_files

                    # Recreates the matrix
                    saved_format.save_matrix(df, matrix_path)
                    # saving the same matrix will migrate its format to the repository one.
                    matrix_content_repo.save(data)
                    saved_matrix_files = list(matrix_content_repo.bucket_dir.glob(f"*.{matrix_format}"))
                    assert not saved_matrix_files
                    repo_matrix_files = list(matrix_content_repo.bucket_dir.glob(f"*.{repository_format}"))
                    assert len(repo_matrix_files) == 1
                    new_matrix_path = matrix_path.with_suffix(f".{repository_format}")
                    assert repo_matrix_files[0] == new_matrix_path
