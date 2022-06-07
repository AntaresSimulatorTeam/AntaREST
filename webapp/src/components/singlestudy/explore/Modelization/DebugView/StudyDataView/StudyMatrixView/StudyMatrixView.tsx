import { useEffect, useState } from "react";
import { AxiosError } from "axios";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { Box, Typography, Divider, ButtonGroup, Button } from "@mui/material";
import TableViewIcon from "@mui/icons-material/TableView";
import BarChartIcon from "@mui/icons-material/BarChart";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import {
  getStudyData,
  importFile,
} from "../../../../../../../services/api/study";
import {
  MatrixIndex,
  MatrixType,
  MatrixEditDTO,
} from "../../../../../../../common/types";
import { Header, Root, Content } from "../style";
import { StyledButton } from "./style";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import NoContent from "../../../../../../common/page/NoContent";
import ImportDialog from "../../../../../../common/dialogs/ImportDialog";
import SimpleLoader from "../../../../../../common/loaders/SimpleLoader";
import EditableMatrix from "../../../../../../common/EditableMatrix";
import {
  editMatrix,
  getStudyMatrixIndex,
} from "../../../../../../../services/api/matrix";

const logErr = debug("antares:createimportform:error");

interface PropTypes {
  study: string;
  url: string;
  filterOut: Array<string>;
}

function StudyMatrixView(props: PropTypes) {
  const { study, url, filterOut } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [data, setData] = useState<MatrixType>();
  const [loaded, setLoaded] = useState(false);
  const [toggleView, setToggleView] = useState(true);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [matrixIndex, setMatrixIndex] = useState<MatrixIndex>();
  const [isEditable, setEditable] = useState(true);
  const [formatedPath, setFormatedPath] = useState("");

  const loadFileData = async () => {
    setData(undefined);
    setLoaded(false);
    try {
      const res = await getStudyData(study, url);
      if (typeof res === "string") {
        const fixed = res.replace(/NaN/g, '"NaN"');
        setData(JSON.parse(fixed));
      } else {
        setData(res);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("data.error.matrix"), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  const onImport = async (file: File) => {
    try {
      await importFile(file, study, formatedPath);
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("variants.error.import"), e as AxiosError);
    } finally {
      enqueueSnackbar(t("variants.success.import"), {
        variant: "success",
      });
      loadFileData();
    }
  };

  const getMatrixIndex = async () => {
    try {
      const res = await getStudyMatrixIndex(study);
      setMatrixIndex(res);
    } catch (e) {
      enqueueErrorSnackbar(t("matrix.failedtoretrieveindex"), e as AxiosError);
    }
  };

  const handleUpdate = async (change: MatrixEditDTO[], source: string) => {
    if (source !== "loadData" && source !== "updateData") {
      try {
        if (change.length > 10) {
          throw new Error(t("matrix.error.tooManyUpdates"));
        }
        await editMatrix(study, formatedPath, change);
        enqueueSnackbar(t("matrix.success.matrixUpdate"), {
          variant: "success",
        });
      } catch (e) {
        enqueueErrorSnackbar(t("matrix.error.matrixUpdate"), e as AxiosError);
      }
    }
  };

  useEffect(() => {
    const urlParts = url.split("/");
    const tmpUrl = urlParts.filter((item) => item);
    setFormatedPath(tmpUrl.join("/"));
    if (tmpUrl.length > 0) {
      setEditable(!filterOut.includes(tmpUrl[0]));
    }
    if (urlParts.length < 2) {
      enqueueSnackbar(t("studies.error.retrieveData"), {
        variant: "error",
      });
      return;
    }
    loadFileData();
    getMatrixIndex();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, filterOut, enqueueSnackbar, t]);

  return (
    <Root>
      <Content>
        <Header>
          <Typography
            sx={{
              color: "text.primary",
              fontSize: "1.25rem",
              fontWeight: 400,
              lineHeight: 1.334,
            }}
          >
            {t("xpansion.timeSeries")}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            {loaded && data && data.columns?.length > 1 && (
              <ButtonGroup sx={{ mr: 2 }} variant="contained">
                <StyledButton
                  onClick={
                    toggleView ? undefined : () => setToggleView(!toggleView)
                  }
                  disabled={toggleView}
                >
                  <TableViewIcon sx={{ color: "text.main" }} />
                </StyledButton>
                <StyledButton
                  onClick={
                    toggleView ? () => setToggleView(!toggleView) : undefined
                  }
                  disabled={!toggleView}
                >
                  <BarChartIcon sx={{ color: "text.main" }} />
                </StyledButton>
              </ButtonGroup>
            )}
            {isEditable && (
              <Button
                variant="outlined"
                color="primary"
                startIcon={<GetAppOutlinedIcon />}
                onClick={() => setOpenImportDialog(true)}
              >
                {t("global.import")}
              </Button>
            )}
          </Box>
        </Header>
        <Divider sx={{ width: "100%", mt: 2, mb: 3 }} />
        {!loaded && <SimpleLoader />}
        {loaded && data && data.columns?.length > 1 ? (
          <EditableMatrix
            matrix={data}
            matrixTime
            matrixIndex={matrixIndex}
            readOnly={!isEditable}
            toggleView={toggleView}
            onUpdate={handleUpdate}
          />
        ) : (
          loaded && (
            <NoContent
              title="matrix.message.matrixEmpty"
              callToAction={
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<GetAppOutlinedIcon />}
                  onClick={() => setOpenImportDialog(true)}
                >
                  {t("global.import")}
                </Button>
              }
            />
          )
        )}
      </Content>
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("matrix.importnewmatrix")}
          dropzoneText={t("matrix.message.importhint")}
          onClose={() => setOpenImportDialog(false)}
          onImport={onImport}
        />
      )}
    </Root>
  );
}

export default StudyMatrixView;
