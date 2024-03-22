import pathlib

import polars as pl
import pytest
from polars.testing import assert_frame_equal
from test import lazyframe_functions

from hamilton.plugins.polars_lazyframe_extensions import (
    PolarsAvroReader,
    PolarsAvroWriter,
    PolarsCSVReader,
    PolarsCSVWriter,
    PolarsFeatherReader,
    PolarsFeatherWriter,
    PolarsJSONReader,
    PolarsJSONWriter,
    PolarsParquetReader,
    PolarsParquetWriter,
)


@pytest.fixture
def df():
    yield pl.LazyFrame({"a": [1, 2], "b": [3, 4]})


def test_driver():

    from hamilton import base, driver
    from hamilton.plugins import h_polars_lazyframe

    polars_builder = h_polars_lazyframe.PolarsDataFrameResult()
    adapter = base.SimplePythonGraphAdapter(polars_builder)
    dr = driver.Driver({}, lazyframe_functions, adapter=adapter)
    df = dr.execute(["do_something"], inputs={})
    print(df)


def test_polars_lazyframe_csv(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"

    writer = PolarsCSVWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsCSVReader(file=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.LazyFrame)

    assert PolarsCSVWriter.applicable_types() == [pl.LazyFrame]
    assert PolarsCSVReader.applicable_types() == [pl.LazyFrame]
    assert kwargs1["separator"] == ","
    assert kwargs2["has_header"] is True
    assert_frame_equal(df.collect(), df2.collect())


def test_polars_parquet(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.parquet"

    writer = PolarsParquetWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsParquetReader(file=file, n_rows=2)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsParquetWriter.applicable_types() == [pl.DataFrame]
    assert PolarsParquetReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["compression"] == "zstd"
    assert kwargs2["n_rows"] == 2
    assert df.frame_equal(df2)


def test_polars_feather(tmp_path: pathlib.Path) -> None:
    test_data_file_path = "tests/resources/data/test_load_from_data.feather"
    reader = PolarsFeatherReader(source=test_data_file_path)
    read_kwargs = reader._get_loading_kwargs()
    df, _ = reader.load_data(pl.DataFrame)

    file_path = tmp_path / "test.dta"
    writer = PolarsFeatherWriter(file=file_path)
    write_kwargs = writer._get_saving_kwargs()
    metadata = writer.save_data(df)

    assert PolarsFeatherReader.applicable_types() == [pl.DataFrame]
    assert "n_rows" not in read_kwargs
    assert df.shape == (4, 3)

    assert PolarsFeatherWriter.applicable_types() == [pl.DataFrame]
    assert "compression" in write_kwargs
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["animal", "points", "environment"]
    assert metadata["dataframe_metadata"]["datatypes"] == ["String", "Int64", "String"]


def test_polars_json(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.json"
    writer = PolarsJSONWriter(file=file, pretty=True)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsJSONReader(source=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsJSONWriter.applicable_types() == [pl.DataFrame]
    assert PolarsJSONReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["pretty"]
    assert df2.shape == (2, 2)
    assert "schema" not in kwargs2
    assert df.frame_equal(df2)


def test_polars_avro(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.avro"

    writer = PolarsAvroWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsAvroReader(file=file, n_rows=2)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsAvroWriter.applicable_types() == [pl.DataFrame]
    assert PolarsAvroReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["compression"] == "uncompressed"
    assert kwargs2["n_rows"] == 2
    assert df.frame_equal(df2)
