from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pytest

from antarest.core.config import Config, SecurityConfig
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Password, User
from antarest.login.repository import GroupRepository, UserRepository
from antarest.matrixstore.model import Matrix, MatrixContent, MatrixDataSet, MatrixDataSetRelation
from antarest.matrixstore.repository import MatrixContentRepository, MatrixDataSetRepository, MatrixRepository


class TestMatrixRepository:
    def test_db_lifecycle(self):
        with db():
            # sourcery skip: extract-method
            repo = MatrixRepository()
            m = Matrix(
                id="hello",
                created_at=datetime.now(),
            )
            repo.save(m)
            assert m.id
            assert m == repo.get(m.id)
            assert repo.exists(m.id)
            repo.delete(m.id)
            assert repo.get(m.id) is None

    def test_bucket_lifecycle(self, tmp_path: Path):
        repo = MatrixContentRepository(tmp_path)

        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]

        matrix_content_a = MatrixContent(data=a, index=[0, 1], columns=[0, 1])
        matrix_content_b = MatrixContent(data=b, index=[0, 1], columns=[0, 1])

        aid = repo.save(a)
        assert aid == repo.save(a)

        bid = repo.save(b)
        assert aid != bid

        assert matrix_content_a == repo.get(aid)
        assert matrix_content_b == repo.get(bid)

        repo.delete(aid)
        with pytest.raises(FileNotFoundError):
            repo.get(aid)

    def test_dataset(self):
        with db():
            # sourcery skip: extract-duplicate-method, extract-method
            repo = MatrixRepository()

            user_repo = UserRepository(Config(security=SecurityConfig()))
            # noinspection PyArgumentList
            user = user_repo.save(User(name="foo", password=Password("bar")))

            group_repo = GroupRepository()
            # noinspection PyArgumentList
            group = group_repo.save(Group(name="group"))

            dataset_repo = MatrixDataSetRepository()

            m1 = Matrix(
                id="hello",
                created_at=datetime.now(),
            )
            repo.save(m1)
            m2 = Matrix(
                id="world",
                created_at=datetime.now(),
            )
            repo.save(m2)

            dataset = MatrixDataSet(
                name="some name",
                public=True,
                owner_id=user.id,
                groups=[group],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            matrix_relation = MatrixDataSetRelation(name="m1")
            matrix_relation.matrix_id = "hello"
            dataset.matrices.append(matrix_relation)
            matrix_relation = MatrixDataSetRelation(name="m2")
            matrix_relation.matrix_id = "world"
            dataset.matrices.append(matrix_relation)

            dataset = dataset_repo.save(dataset)
            dataset_query_result: Optional[MatrixDataSet] = dataset_repo.get(
                dataset.id
            )
            assert dataset_query_result is not None
            assert dataset_query_result.name == "some name"
            assert len(dataset_query_result.matrices) == 2

            dataset_update = MatrixDataSet(
                id=dataset.id,
                name="some name change",
                public=False,
                updated_at=datetime.now(),
            )
            dataset_repo.save(dataset_update)
            dataset_query_result: Optional[MatrixDataSet] = dataset_repo.get(
                dataset.id
            )
            assert dataset_query_result is not None
            assert dataset_query_result.name == "some name change"
            assert dataset_query_result.owner_id == user.id

    def test_datastore_query(self):
        # sourcery skip: extract-duplicate-method
        with db():
            user_repo = UserRepository(Config(security=SecurityConfig()))
            # noinspection PyArgumentList
            user1 = user_repo.save(User(name="foo", password=Password("bar")))
            # noinspection PyArgumentList
            user2 = user_repo.save(
                User(name="hello", password=Password("world"))
            )

            repo = MatrixRepository()
            m1 = Matrix(
                id="hello",
                created_at=datetime.now(),
            )
            repo.save(m1)
            m2 = Matrix(
                id="world",
                created_at=datetime.now(),
            )
            repo.save(m2)

            dataset_repo = MatrixDataSetRepository()

            dataset = MatrixDataSet(
                name="some name",
                public=True,
                owner_id=user1.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
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
                created_at=datetime.now(),
                updated_at=datetime.now(),
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
                len(
                    db.session.query(MatrixDataSetRelation)
                    .filter(MatrixDataSetRelation.dataset_id == dataset.id)
                    .all()
                )
                == 0
            )


class TestMatrixContentRepository:
    def test_save(self, matrix_content_repo: MatrixContentRepository):
        """
        Saves the content of a matrix as a TSV file in the directory
        and returns its SHA256 hash.
        """
        # sourcery skip: extract-duplicate-method
        bucket_dir = matrix_content_repo.bucket_dir

        # when the data is saved in the repo
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_hash = matrix_content_repo.save(data)
        # then a TSV file is created in the repo directory
        matrix_file = bucket_dir.joinpath(f"{matrix_hash}.tsv")
        array = np.loadtxt(
            matrix_file, delimiter="\t", dtype=np.float64, ndmin=2
        )
        assert array.tolist() == data
        modif_time = matrix_file.stat().st_mtime

        # when the data is saved again with same float values
        data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        matrix_content_repo.save(data)
        # then no new TSV file is created
        matrix_files = list(bucket_dir.glob("*.tsv"))
        assert matrix_files == [matrix_file]
        assert matrix_file.stat().st_mtime == modif_time, "date changed!"

        # when the data is saved again as NumPy array
        data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
        matrix_content_repo.save(data)
        # then no new TSV file is created
        matrix_files = list(bucket_dir.glob("*.tsv"))
        assert matrix_files == [matrix_file]
        assert matrix_file.stat().st_mtime == modif_time, "date changed!"

        # when other data is saved with different values
        other_data = [[9.0, 2.0, 3.0], [10.0, 20.0, 30.0]]
        other_matrix_hash = matrix_content_repo.save(other_data)
        # then a new TSV file is created
        matrix_files = list(bucket_dir.glob("*.tsv"))
        other_matrix_file = bucket_dir.joinpath(f"{other_matrix_hash}.tsv")
        assert set(matrix_files) == {matrix_file, other_matrix_file}

    def test_get(self, matrix_content_repo):
        """
        Retrieves the content of a matrix with a given SHA256 hash.
        """
        # when the data is saved in the repo
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_hash = matrix_content_repo.save(data)
        # then the saved matrix object can be retrieved
        content = matrix_content_repo.get(matrix_hash)
        assert content.index == list(range(len(data)))
        assert content.columns == list(range(len(data[0])))
        assert content.data == data

        # when the data is missing (wrong SHA256)
        # then a `FileNotFoundError` is raised
        with pytest.raises(FileNotFoundError):
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            matrix_content_repo.get(missing_hash)

    def test_exists(self, matrix_content_repo):
        """
        Checks if a matrix with a given SHA256 hash exists in the directory.
        """
        # when the data is saved in the repo
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_hash = matrix_content_repo.save(data)
        # then the saved matrix object exists
        assert matrix_content_repo.exists(matrix_hash)

        # when the data is missing (wrong SHA256)
        # then the saved matrix object doesn't exist
        missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
        assert not matrix_content_repo.exists(missing_hash)

    def test_delete(self, matrix_content_repo):
        """
        Deletes the tsv file containing the content of a matrix with a given SHA256 hash.
        """
        # when the data is saved in the repo
        data = [[1, 2, 3], [4, 5, 6]]
        matrix_hash = matrix_content_repo.save(data)
        # then the saved matrix object can be deleted
        matrix_content_repo.delete(matrix_hash)
        # and the file doesn't exist anymore
        matrix_files = list(matrix_content_repo.bucket_dir.glob("*.tsv"))
        assert not matrix_files

        # when the data is missing (wrong SHA256)
        # then a `FileNotFoundError` is raised
        with pytest.raises(FileNotFoundError):
            missing_hash = "8b1a9953c4611296a827abf8c47804d7e6c49c6b"
            matrix_content_repo.delete(missing_hash)
