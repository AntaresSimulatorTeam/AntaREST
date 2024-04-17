import { StudyMetadata } from "../../common/types";
import usePromise from "../../hooks/usePromise";
import {
  getTableMode,
  setTableMode,
} from "../../services/api/studies/tableMode";
import {
  TableData,
  TableModeColumnsForType,
  TableModeType,
} from "../../services/api/studies/tableMode/types";
import { SubmitHandlerPlus } from "./Form/types";
import TableForm from "./TableForm";
import UsePromiseCond from "./utils/UsePromiseCond";

export interface TableModeProps<T extends TableModeType = TableModeType> {
  studyId: StudyMetadata["id"];
  type: T;
  columns: TableModeColumnsForType<T>;
}

function TableMode<T extends TableModeType>(props: TableModeProps<T>) {
  const { studyId, type, columns } = props;

  const res = usePromise(
    () => getTableMode({ studyId, type, columns }),
    [studyId, type, JSON.stringify(columns)],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<TableData>) => {
    return setTableMode({ studyId, type, data: data.dirtyValues });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(data) => (
        <TableForm
          defaultValues={data}
          onSubmit={handleSubmit}
          tableProps={{ columns }}
          autoSubmit={false}
        />
      )}
    />
  );
}

export default TableMode;
