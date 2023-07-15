import collections
import io
import typing as t

from pydantic import (
    BaseModel as CoreBaseModel,
    Extra,
    Field,
)

from antarest.core.utils.string import to_camel_case

OperationType = t.Callable[[t.Iterable[float]], float]


class BaseModel(CoreBaseModel):
    """
    Pydantic Model for TableGroup
    """

    class Config:
        alias_generator = to_camel_case
        extra = Extra.forbid
        validate_assignment = True
        allow_population_by_field_name = True


class TableGroup(BaseModel):
    """
    Represents a table or a group of tables.

    The purpose of this class is to provide a flexible and recursive structure for managing
    tabular data that can be displayed in a web application or processed programmatically.
    It allows for the creation of complex tables with multiple levels of nesting, such as
    groups within groups.

    The `TableGroup` class also provides methods for calculating operations on columns.

    Attributes:
        properties: A dictionary representing column names and their associated values.
        elements: A dictionary representing child elements of the table group.
        operations: A dictionary representing operations to perform on columns.
    """

    properties: t.Dict[str, t.Any] = {}
    elements: t.Dict[str, "TableGroup"] = {}
    operations: t.Dict[str, OperationType] = Field(
        default_factory=dict,
        exclude=True,
        description="Operation to perform on columns (sum, mean...)",
    )

    def calc_operations(self) -> None:
        """
        Recursively calculates the operations on the table group and its child elements.
        """

        if not self.elements:
            return

        # First update the sums of the children elements.
        for element in self.elements.values():
            element.calc_operations()

        # Create a mapping between columns and column properties.
        columns_map = collections.defaultdict(list)
        for element in self.elements.values():
            for column, data in element.properties.items():
                columns_map[column].append(data)

        # Update (or create) the properties which contain sums.
        for column, data_list in columns_map.items():
            self.properties.setdefault(column, "")  # avoid None!
            if column in self.operations:
                operation = self.operations[column]
                self.properties[column] = operation(data_list)

        # The sorting of properties is necessary to ensure that the values appear
        # in the same order at all levels within the `TableGroup` hierarchy.
        # This order will be preserved when serializing the data to JSON format.
        column_order = {c: i for i, c in enumerate(columns_map)}
        order_by = lambda i: column_order[i[0]]
        self.properties = dict(sorted(self.properties.items(), key=order_by))

    def __str__(self) -> str:
        """
        Returns a string representation of the table group.
        """
        buffer = io.StringIO()
        _TableGroupPrinter().print(self, file=buffer)
        return buffer.getvalue()


class _TableGroupPrinter:
    """
    Print a TableGroup (implementation detail)
    """

    def calc_widths(self, tg: TableGroup) -> t.List[int]:
        """
        Recursively calculate the width of each column.
        """
        widths = [max(len(p), len(str(v))) for p, v in tg.properties.items()]
        matrix = [widths] + [self.calc_widths(e) for e in tg.elements.values()]
        return [max(column) for column in zip(*matrix)]

    def print(
        self,
        tg: TableGroup,
        *,
        level: int = 1,
        gutter: str = " | ",
        widths: t.Sequence[int] = (),
        file: t.Optional[t.IO[str]] = None,
    ) -> None:
        widths = widths or self.calc_widths(tg)
        properties = tg.properties
        values = [
            (
                str(v).rjust(w)
                if isinstance(v, (int, float))
                else str(v).ljust(w)
            )
            for (p, v), w in zip(properties.items(), widths)
        ]
        if elements := tg.elements:
            header = [p.center(w) for p, w in zip(properties, widths)]
            symbol = {1: "=", 2: "-"}.get(level, "+")
            underlines = [symbol * w for w in widths]
            print(gutter.join(underlines), file=file)
            print(gutter.join(header), file=file)
            print(gutter.join(values), file=file)
            print(gutter.join(underlines), file=file)
            for element in elements.values():
                self.print(
                    element,
                    level=level + 1,
                    widths=widths,
                    gutter=gutter,
                    file=file,
                )
        else:
            print(gutter.join(values), file=file)
