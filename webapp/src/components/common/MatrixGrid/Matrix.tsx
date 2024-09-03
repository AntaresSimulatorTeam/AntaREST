import { Divider, Skeleton } from "@mui/material";
import MatrixGrid from ".";
import { useMatrix } from "./useMatrix";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import ImportDialog from "../dialogs/ImportDialog";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../common/types";
import { MatrixContainer, MatrixHeader, MatrixTitle } from "./style";
import MatrixActions from "./MatrixActions";

interface MatrixProps {
  url: string;
  title?: string;
  enableTimeSeriesColumns?: boolean;
  enableAggregateColumns?: boolean;
}

function Matrix({
  url,
  title = "global.timeSeries",
  enableTimeSeriesColumns = true,
  enableAggregateColumns = false,
}: MatrixProps) {
  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [openImportDialog, setOpenImportDialog] = useState(false);

  const {
    matrixData,
    isLoading,
    columns,
    dateTime,
    handleCellEdit,
    handleMultipleCellsEdit,
    handleImport,
  } = useMatrix(study.id, url, enableTimeSeriesColumns, enableAggregateColumns);

  if (isLoading || !matrixData) {
    return <Skeleton sx={{ height: 1, transform: "none" }} />;
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <MatrixContainer>
      <MatrixHeader>
        <MatrixTitle>{t(title)}</MatrixTitle>
        <MatrixActions
          onImport={() => setOpenImportDialog(true)}
          studyId={study.id}
          path={url}
          disabled={matrixData.data.length === 0}
        />
      </MatrixHeader>

      <Divider sx={{ width: 1, mt: 1, mb: 2 }} />

      <MatrixGrid
        data={matrixData.data}
        columns={columns}
        rows={matrixData.data.length}
        dateTime={dateTime}
        onCellEdit={handleCellEdit}
        onMultipleCellsEdit={handleMultipleCellsEdit}
      />

      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("matrix.importNewMatrix")}
          dropzoneText={t("matrix.message.importHint")}
          onCancel={() => setOpenImportDialog(false)}
          onImport={handleImport}
          accept={{ "text/*": [".csv", ".tsv", ".txt"] }}
        />
      )}
    </MatrixContainer>
  );
}

export default Matrix;
