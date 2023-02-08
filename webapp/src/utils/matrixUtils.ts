import { MatrixType } from "../common/types";

export function downloadMatrix(matrixData: MatrixType, fileName: string): void {
  const fileData = matrixData.data.map((row) => row.join("\t")).join("\n");
  const blob = new Blob([fileData], { type: "text/plain" });
  const a = document.createElement("a");
  a.download = fileName;
  a.href = URL.createObjectURL(blob);
  a.click();
  URL.revokeObjectURL(a.href);
}
