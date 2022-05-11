import { useState, useEffect } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { MatrixInfoDTO, MatrixType } from "../../common/types";
import MatrixView from "../common/MatrixView";
import BasicDialog from "../common/dialogs/BasicDialog";
import { getMatrix } from "../../services/api/matrix";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import NoContent from "../common/page/NoContent";
import SimpleLoader from "../common/loaders/SimpleLoader";

interface PropTypes {
  matrixInfo: MatrixInfoDTO;
  open: boolean;
  onClose: () => void;
}

function MatrixDialog(props: PropTypes) {
  const { matrixInfo, open, onClose } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);
  const [matrix, setCurrentMatrix] = useState<MatrixType>({
    index: [],
    columns: [],
    data: [],
  });

  const copyId = (matrixId: string): void => {
    try {
      navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t("data:onMatrixIdCopySuccess"), { variant: "success" });
    } catch (e) {
      enqueueSnackbar(t("data:onMatrixIdCopyError"), { variant: "error" });
    }
  };

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
        enqueueErrorSnackbar(t("data:matrixError"), error as AxiosError);
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

  return (
    <BasicDialog
      open={open}
      title={`Matrix - ${matrixInfo.name}`}
      onClose={onClose}
      fullWidth
      maxWidth="lg"
    >
      <Box sx={{ height: "60vh" }}>
        {loading && <SimpleLoader />}
        {matrix.columns.length > 0 ? (
          <MatrixView readOnly matrix={matrix} />
        ) : (
          !loading && (
            <Box
              sx={{
                width: "100%",
                height: "100%",
                pt: "3%",
              }}
            >
              <NoContent title="data:matrixEmpty" />
            </Box>
          )
        )}
      </Box>
    </BasicDialog>
  );
}

export default MatrixDialog;
