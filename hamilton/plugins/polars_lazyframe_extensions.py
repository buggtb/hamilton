import dataclasses
from io import BytesIO, IOBase, TextIOWrapper
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    Collection,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Type,
    Union,
)

try:
    import polars as pl
    from polars import PolarsDataType
except ImportError:
    raise NotImplementedError("Polars is not installed.")


# for polars <0.16.0 we need to determine whether type_aliases exist.
has_alias = False
if hasattr(pl, "type_aliases"):
    has_alias = True

# for polars 0.18.0 we need to check what to do.
if has_alias and hasattr(pl.type_aliases, "CsvEncoding"):
    from polars.type_aliases import CsvEncoding
else:
    CsvEncoding = Type


from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataLoader, DataSaver

DATAFRAME_TYPE = pl.LazyFrame
COLUMN_TYPE = pl.LazyFrame



@registry.get_column.register(pl.LazyFrame)
def get_column_polars_lazyframe(df: pl.LazyFrame, column_name: str) -> pl.LazyFrame:
    return df.select(column_name)


@registry.fill_with_scalar.register(pl.LazyFrame)
def fill_with_scalar_polars_lazyframe(
    df: pl.LazyFrame, column_name: str, scalar_value: Any
) -> pl.LazyFrame:
    if not isinstance(scalar_value, pl.Series):
        scalar_value = [scalar_value]
    return df.with_columns(pl.Series(name=column_name, values=scalar_value))


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("polars_lazyframe", DATAFRAME_TYPE, COLUMN_TYPE)


register_types()


@dataclasses.dataclass
class PolarsCSVReader(DataLoader):
    """Class specifically to handle loading CSV files with Polars.
    Should map to https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.read_csv.html
    """

    file: Union[str, TextIO, BytesIO, Path, BinaryIO, bytes]
    # kwargs:
    has_header: bool = True
    columns: Union[Sequence[int], Sequence[str]] = None
    new_columns: Sequence[str] = None
    separator: str = ","
    comment_char: str = None
    quote_char: str = '"'
    skip_rows: int = 0
    dtypes: Union[Mapping[str, PolarsDataType], Sequence[PolarsDataType]] = None
    null_values: Union[str, Sequence[str], Dict[str, str]] = None
    missing_utf8_is_empty_string: bool = False
    ignore_errors: bool = False
    try_parse_dates: bool = False
    n_threads: int = None
    infer_schema_length: int = 100
    batch_size: int = 8192
    n_rows: int = None
    encoding: Union[CsvEncoding, str] = "utf8"
    low_memory: bool = False
    rechunk: bool = True
    use_pyarrow: bool = False
    storage_options: Dict[str, Any] = None
    skip_rows_after_header: int = 0
    row_count_name: str = None
    row_count_offset: int = 0
    eol_char: str = "\n"
    raise_if_empty: bool = True


    def _get_loading_kwargs(self):
        kwargs = {}
        if self.has_header is not None:
            kwargs["has_header"] = self.has_header
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.new_columns is not None:
            kwargs["new_columns"] = self.new_columns
        if self.separator is not None:
            kwargs["separator"] = self.separator
        if self.comment_char is not None:
            kwargs["comment_char"] = self.comment_char
        if self.quote_char is not None:
            kwargs["quote_char"] = self.quote_char
        if self.skip_rows is not None:
            kwargs["skip_rows"] = self.skip_rows
        if self.dtypes is not None:
            kwargs["dtypes"] = self.dtypes
        if self.null_values is not None:
            kwargs["null_values"] = self.null_values
        if self.missing_utf8_is_empty_string is not None:
            kwargs["missing_utf8_is_empty_string"] = self.missing_utf8_is_empty_string
        if self.ignore_errors is not None:
            kwargs["ignore_errors"] = self.ignore_errors
        if self.try_parse_dates is not None:
            kwargs["try_parse_dates"] = self.try_parse_dates
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads
        if self.infer_schema_length is not None:
            kwargs["infer_schema_length"] = self.infer_schema_length
        if self.n_rows is not None:
            kwargs["n_rows"] = self.n_rows
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.low_memory is not None:
            kwargs["low_memory"] = self.low_memory
        if self.rechunk is not None:
            kwargs["rechunk"] = self.rechunk
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.skip_rows_after_header is not None:
            kwargs["skip_rows_after_header"] = self.skip_rows_after_header
        if self.row_count_name is not None:
            kwargs["row_count_name"] = self.row_count_name
        if self.row_count_offset is not None:
            kwargs["row_count_offset"] = self.row_count_offset
        if self.eol_char is not None:
            kwargs["eol_char"] = self.eol_char
        if self.raise_if_empty is not None:
            kwargs["raise_if_empty"] = self.raise_if_empty
        return kwargs

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [DATAFRAME_TYPE]



    def load_data(self, type_: Type) -> Tuple[DATAFRAME_TYPE, Dict[str, Any]]:
        df = pl.scan_csv(self.file, **self._get_loading_kwargs())

        metadata = utils.get_file_and_dataframe_metadata(self.file, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "csv"



def register_data_loaders():
    """Function to register the data loaders for this extension."""
    for loader in [
        PolarsCSVReader,
    ]:
        registry.register_adapter(loader)


register_data_loaders()
