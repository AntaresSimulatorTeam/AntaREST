import { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { MatrixInfoDTO, MatrixType } from "../../common/types";
import { getMatrix } from "../../services/api/matrix";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import DataViewerDialog from "../common/dialogs/DataViewerDialog";

interface PropTypes {
  matrixInfo: MatrixInfoDTO;
  open: boolean;
  onClose: () => void;
}

function MatrixDialog(props: PropTypes) {
  const { matrixInfo, open, onClose } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [loading, setLoading] = useState(false);
  const [matrix, setCurrentMatrix] = useState<MatrixType>({
    index: [],
    columns: [],
    data: [],
  });

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        if (matrixInfo) {
          const res = await getMatrix(matrixInfo.id);
          const matrixContent: MatrixType = {
            index: matrix ? res.index : [],
            columns: matrix ? res.columns : [],
            data: matrix ? res.data : [],
          };
          setCurrentMatrix(matrixContent);
        }
      } catch (error) {
        enqueueErrorSnackbar(t("data.error.matrix"), error as AxiosError);
      } finally {
        setLoading(false);
      }
    };
    init();
    return () => {
      setCurrentMatrix({ index: [], columns: [], data: [] });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enqueueErrorSnackbar, matrixInfo, t]);

  return open ? (
    <DataViewerDialog
      filename={matrixInfo.name}
      onClose={onClose}
      loading={loading}
      content={{ ...matrix, id: matrixInfo.id }}
      isMatrix
    />
  ) : (
    <div />
  );
}

export default MatrixDialog;
