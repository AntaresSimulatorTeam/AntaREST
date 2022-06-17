import { useState, useEffect, forwardRef, ChangeEvent } from "react";
import {
  Box,
  TextField,
  Typography,
  Button,
  Checkbox,
  Chip,
  Tooltip,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import axios, { AxiosError } from "axios";
import HelpIcon from "@mui/icons-material/Help";
import { getGroups } from "../../services/api/user";
import { GroupDTO, MatrixDataSetDTO } from "../../common/types";
import { saveMatrix } from "./utils";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import SimpleLoader from "../common/loaders/SimpleLoader";
import BasicDialog from "../common/dialogs/BasicDialog";
import { BoxParamHeader, BoxParam, ParamTitle } from "./styles";

interface PropTypes {
  open: boolean;
  onNewDataUpdate: (newData: MatrixDataSetDTO) => void;
  data: MatrixDataSetDTO | undefined;
  onClose: () => void;
}

const HelperIcon = forwardRef<HTMLInputElement>((props, ref) => {
  if (ref) {
    return (
      <span {...props} style={{ marginLeft: "0.5em" }} ref={ref}>
        <HelpIcon />
      </span>
    );
  }
  return <div />;
});

HelperIcon.displayName = "HelperIcon";

function DatasetCreationDialog(props: PropTypes) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const { open, onNewDataUpdate, onClose, data } = props;
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [selectedGroupList, setSelectedGroupList] = useState<Array<GroupDTO>>(
    []
  );
  const [name, setName] = useState<string>("");
  const [isJson, setIsJson] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [currentFile, setFile] = useState<File | undefined>();
  const [importing, setImporting] = useState(false);
  const [publicStatus, setPublic] = useState<boolean>(false);

  const onSave = async () => {
    let closeModal = true;
    try {
      setImporting(true);
      const msg = await saveMatrix(
        name,
        publicStatus,
        selectedGroupList,
        onNewDataUpdate,
        currentFile,
        data,
        isJson,
        setUploadProgress
      );
      enqueueSnackbar(t(msg), { variant: "success" });
    } catch (e) {
      if (axios.isAxiosError(e)) {
        enqueueErrorSnackbar(t(e.message), e as AxiosError);
      } else {
        const error = e as Error;
        enqueueSnackbar(t(error.message), { variant: "error" });
        if (
          error.message === "data.error.fileNotUploaded" ||
          error.message === "global.error.emptyName"
        )
          closeModal = false;
      }
    } finally {
      setImporting(false);
      if (closeModal) onClose();
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const onUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const { target } = e;
    if (target && target.files && target.files.length === 1) {
      setFile(target.files[0]);
    }
  };

  const onGroupClick = (add: boolean, item: GroupDTO) => {
    if (add) {
      setSelectedGroupList(selectedGroupList.concat([item]));
    } else {
      setSelectedGroupList(
        selectedGroupList.filter((elm) => item.id !== elm.id)
      );
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const groups = await getGroups();
        const filteredGroup = groups.filter((item) => item.id !== "admin");
        setGroupList(filteredGroup);

        if (data) {
          setSelectedGroupList(data.groups);
          setPublic(data.public);
          setName(data.name);
        }
      } catch (e) {
        enqueueSnackbar(t("settings.error.groupsError"), {
          variant: "error",
        });
      }
    };
    init();
    return () => {
      setGroupList([]);
    };
  }, [data, t, enqueueSnackbar]);

  const renderContent = () => {
    if (importing) {
      return (
        <Box sx={{ height: "200px", width: "100%" }}>
          {uploadProgress < 100 ? (
            <SimpleLoader
              message="data.uploadingmatrix"
              progress={uploadProgress}
            />
          ) : (
            <SimpleLoader message="data.analyzingmatrix" />
          )}
        </Box>
      );
    }
    return (
      <>
        <Box
          sx={{
            flex: "1",
            width: "100%",
            display: "flex",
            flexFlow: "column nowrap",
            justifyContent: "flex-start",
            alignItems: "flex-start",
            p: 2,
            mb: 1,
          }}
        >
          <TextField
            sx={{
              width: "400px",
              height: "30px",
              boxSizing: "border-box",
              m: 2,
            }}
            size="small"
            value={name}
            onChange={(event) => setName(event.target.value as string)}
            label={t("data.matrixName")}
            variant="outlined"
          />
          {!data && (
            <Box
              sx={{
                width: "400px",
                height: "30px",
                boxSizing: "border-box",
                m: 2,
              }}
            >
              <input
                style={{
                  display: "none",
                }}
                id="upload-file"
                accept=".csv, .txt, .zip"
                onChange={onUpload}
                type="file"
              />
              <label
                htmlFor="upload-file"
                style={{
                  display: "flex",
                  flexFlow: "row nowrap",
                  justifyContent: "flex-start",
                  alignItems: "center",
                }}
              >
                <Button
                  sx={{
                    p: 1,
                    height: "30px",
                    "&:hover": {
                      borderColor: "secondary.main",
                      color: "secondary.main",
                    },
                    mr: 1,
                  }}
                  variant="outlined"
                  color="primary"
                  component="span"
                >
                  {t("global.upload")}
                </Button>
                <Typography
                  noWrap
                  sx={{
                    color: "action.active",
                  }}
                >
                  {currentFile ? currentFile.name : t("global.chooseFile")}
                </Typography>
                <Tooltip
                  title={t("data.message.uploadHelp") as string}
                  placement="top"
                >
                  <HelperIcon />
                </Tooltip>
              </label>
            </Box>
          )}
        </Box>
        <BoxParam>
          <BoxParamHeader>
            <ParamTitle>{t("data.jsonFormat")}</ParamTitle>
            <Checkbox
              checked={isJson}
              onChange={() => setIsJson(!isJson)}
              inputProps={{ "aria-label": "primary checkbox" }}
            />
          </BoxParamHeader>
        </BoxParam>
        <BoxParam>
          <BoxParamHeader>
            <ParamTitle>{t("global.public")}</ParamTitle>
            <Checkbox
              checked={publicStatus}
              onChange={() => setPublic(!publicStatus)}
              inputProps={{ "aria-label": "primary checkbox" }}
            />
          </BoxParamHeader>
        </BoxParam>
        {!publicStatus && (
          <BoxParam>
            <BoxParamHeader>
              <ParamTitle>{t("global.groups")}</ParamTitle>
            </BoxParamHeader>
            <Box
              sx={{
                width: "100%",
                display: "flex",
                flexFlow: "row nowrap",
                justifyContent: "flex-start",
                alignItems: "flex-start",
                flexWrap: "wrap",
                "& > *": {
                  m: "4px !important",
                },
              }}
            >
              {groupList.map((item) => {
                const index = selectedGroupList.findIndex(
                  (elm) => item.id === elm.id
                );
                if (index >= 0) {
                  return (
                    <Chip
                      key={item.id}
                      label={item.name}
                      onClick={() => onGroupClick(false, item)}
                      color="secondary"
                    />
                  );
                }
                return (
                  <Chip
                    key={item.id}
                    label={item.name}
                    onClick={() => onGroupClick(true, item)}
                  />
                );
              })}
            </Box>
          </BoxParam>
        )}
      </>
    );
  };

  return (
    <BasicDialog
      open={open}
      onClose={!importing ? onClose : undefined}
      title={data ? data.name : t("data.newMatrixTitle")}
      actions={
        !importing && (
          <Box>
            <Button color="primary" onClick={onClose} sx={{ m: 2 }}>
              {t("button.cancel")}
            </Button>
            <Button variant="contained" onClick={onSave} sx={{ m: 2 }}>
              {t("button.save")}
            </Button>
          </Box>
        )
      }
    >
      <Box
        sx={{
          flex: "1",
          width: "100%",
          display: "flex",
          flexFlow: "column nowrap",
          justifyContent: "flex-start",
          alignItems: "center",
          overflowY: "auto",
          overflowX: "hidden",
          position: "relative",
        }}
      >
        {renderContent()}
      </Box>
    </BasicDialog>
  );
}

export default DatasetCreationDialog;
