import { downloadMatrix } from "../../../services/api/studies/raw";
import { downloadFile } from "../../../utils/fileUtils";
import { StudyMetadata } from "../../../common/types";
import { useTranslation } from "react-i18next";
import DownloadButton from "./DownloadButton";

export interface DownloadMatrixButtonProps {
  studyId: StudyMetadata["id"];
  path: string;
  disabled?: boolean;
  label?: string;
}

const EXPORT_OPTIONS = [
  { label: "TSV", value: "tsv" },
  { label: "Excel", value: "xlsx" },
] as const;

type ExportFormat = (typeof EXPORT_OPTIONS)[number]["value"];

function DownloadMatrixButton(props: DownloadMatrixButtonProps) {
  const { t } = useTranslation();
  const { studyId, path, disabled, label = t("global.export") } = props;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async (format: ExportFormat) => {
    if (!path) {
      return;
    }

    const isExcel = format === "xlsx";

    const res = await downloadMatrix({
      studyId,
      path,
      format,
      header: isExcel,
      index: isExcel,
    });

    return downloadFile(
      res,
      `matrix_${studyId}_${path.replace("/", "_")}.${format}`,
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DownloadButton
      formatOptions={[...EXPORT_OPTIONS]}
      onClick={handleDownload}
      disabled={!path || disabled}
    >
      {label}
    </DownloadButton>
  );
}

export default DownloadMatrixButton;
