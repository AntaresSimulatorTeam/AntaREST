import TextFileComponent from "./Text";
import JsonFileComponent from "./Json";
import MatrixFileComponent from "./Matrix";
import { FileType } from "../utils";

interface Props {
  studyId: string;
  fileType: FileType;
  filePath: string;
}

const ComponentByFileType = {
  matrix: MatrixFileComponent,
  json: JsonFileComponent,
  file: TextFileComponent,
} as const;

function Data({ studyId, fileType, filePath }: Props) {
  const DataViewer = ComponentByFileType[fileType];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <DataViewer studyId={studyId} path={filePath} />;
}

export default Data;
