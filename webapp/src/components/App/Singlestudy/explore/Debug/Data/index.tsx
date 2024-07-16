import Text from "./Text";
import Json from "./Json";
import Matrix from "./Matrix";
import type { FileInfo } from "../utils";
import { Box } from "@mui/material";

interface Props extends FileInfo {
  studyId: string;
}

const componentByFileType = {
  matrix: Matrix,
  json: Json,
  file: Text,
  folder: Box,
} as const;

function Data({ studyId, fileType, filePath }: Props) {
  const DataViewer = componentByFileType[fileType];

  return <DataViewer studyId={studyId} path={filePath} />;
}

export default Data;
