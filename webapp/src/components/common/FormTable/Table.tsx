import type { RowObject } from "handsontable/common";
import type { IdType } from "../../../common/types";
import { useFormContext } from "../Form";
import Handsontable, { HandsontableProps } from "../Handsontable";

interface Props {
  data: Array<{ id: IdType } & RowObject>;
  columns: NonNullable<HandsontableProps["columns"]>;
}

function Table(props: Props) {
  const { data, columns } = props;
  const { setValue } = useFormContext();
  const rowHeaderWidth =
    data.reduce((longestIdLength, row) => {
      const idLength = row.id.toString().length;
      return longestIdLength > idLength ? longestIdLength : idLength;
    }, 0) * 7.5;

  return (
    <Handsontable
      data={data}
      columns={columns}
      rowHeaders={(index) => String(data[index].id)}
      afterChange={(changes) => {
        changes?.forEach(([row, column, prevValue, nextValue]) => {
          setValue(`${data[row].id}.${column}`, nextValue);
        });
      }}
      allowInvalid={false}
      rowHeaderWidth={rowHeaderWidth}
      height="100%"
      width="100%"
      manualColumnResize
      manualRowResize
    />
  );
}

export default Table;
