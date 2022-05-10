import { useState, useEffect, Fragment } from "react";
import { AxiosError } from "axios";
import {
  Typography,
  List,
  ListItem,
  Collapse,
  Tooltip,
  Box,
} from "@mui/material";
import CreateIcon from "@mui/icons-material/Create";
import DeleteIcon from "@mui/icons-material/HighlightOff";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { MatrixDataSetDTO, MatrixInfoDTO, UserInfo } from "../../common/types";
import { CopyIcon } from "./utils";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";

interface PropTypes {
  data: Array<MatrixDataSetDTO>;
  filter: string;
  user: UserInfo | undefined;
  onDeleteClick: (datasetId: string) => void;
  onUpdateClick: (datasetId: string) => void;
  onMatrixClick: (matrixInfo: MatrixInfoDTO) => void;
}

function DataView(props: PropTypes) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { data, user, filter, onDeleteClick, onUpdateClick, onMatrixClick } =
    props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [toogleList, setToogleList] = useState<Array<boolean>>([]);

  const onButtonChange = (index: number) => {
    if (index >= 0 && index < toogleList.length) {
      const tmpList = ([] as Array<boolean>).concat(toogleList);
      tmpList[index] = !tmpList[index];
      setToogleList(tmpList);
    }
  };

  const copyId = (matrixId: string): void => {
    try {
      navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t("data:onMatrixIdCopySuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("data:onMatrixIdCopyError"), e as AxiosError);
    }
  };

  const matchFilter = (input: string): boolean => input.search(filter) >= 0;

  useEffect(() => {
    const initToogleList: Array<boolean> = [];
    for (let i = 0; i < data.length; i += 1) {
      initToogleList.push(false);
    }
    setToogleList(initToogleList);
  }, [data.length]);

  return (
    <List
      component="nav"
      aria-labelledby="nested-list-subheader"
      sx={{
        flex: "none",
        width: "80%",
        display: "flex",
        padding: 0,
        flexFlow: "column nowrap",
        justifyContent: "flex-start",
        color: "primary.main",
        margin: 3,
      }}
    >
      {data.map(
        (dataset, index) =>
          matchFilter(dataset.name) && (
            <Fragment key={dataset.id}>
              <ListItem
                button
                onClick={() => onButtonChange(index)}
                sx={{
                  display: "flex",
                  padding: 1,
                  pl: 2,
                  flexFlow: "row nowrap",
                  justifyContent: "flex-start",
                  color: "primary.main",
                  backgroundColor: "white",
                  borderRadius: "5px",
                  borderLeft: "7px solid primary.main",
                  margin: 0.2,
                  height: "50px",
                  "&:hover": {
                    backgroundColor: "action.hover",
                  },
                }}
              >
                <Typography
                  sx={{
                    backgroundColor: "action.selected",
                    px: 1,
                    borderRadius: "5px",
                    cursor: "pointer",
                    fontWeight: "bold",
                  }}
                >
                  {dataset.name}
                </Typography>
                <Box
                  sx={{
                    flex: "1",
                    display: "flex",
                    flexFlow: "row nowrap",
                    justifyContent: "flex-end",
                    alignItems: "center",
                  }}
                >
                  {user && user.id === dataset.owner.id && (
                    <>
                      <CreateIcon
                        onClick={() => onUpdateClick(dataset.id)}
                        sx={{
                          color: "primary.main",
                          "&:hover": {
                            color: "primary.light",
                          },
                        }}
                      />
                      <DeleteIcon
                        onClick={() => onDeleteClick(dataset.id)}
                        sx={{
                          color: "error.light",
                          mx: 2,
                          "&:hover": {
                            color: "error.main",
                          },
                        }}
                      />
                    </>
                  )}
                </Box>
                {toogleList[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItem>
              <Collapse in={toogleList[index]} timeout="auto" unmountOnExit>
                <List
                  component="div"
                  disablePadding
                  sx={{
                    display: "flex",
                    pl: 4,
                    flexFlow: "column nowrap",
                    justifyContent: "flex-start",
                  }}
                >
                  {dataset.matrices.map((matrixItem) => (
                    <ListItem
                      key={matrixItem.name}
                      sx={{
                        backgroundColor: "white",
                        margin: 0.2,
                        display: "flex",
                        flexFlow: "row nowrap",
                        justifyContent: "flex-start",
                        alignItems: "center",
                        "&:hover": {
                          backgroundColor: "action.hover",
                        },
                      }}
                    >
                      <Tooltip
                        title={t("data:copyid") as string}
                        placement="top"
                      >
                        <CopyIcon
                          style={{ marginRight: "0.5em", cursor: "pointer" }}
                          onClick={() => copyId(matrixItem.id)}
                        />
                      </Tooltip>
                      <Tooltip title={matrixItem.id} placement="top">
                        <Typography
                          onClick={() => onMatrixClick(matrixItem)}
                          sx={{
                            backgroundColor: "action.selected",
                            px: 1,
                            borderRadius: "5px",
                            cursor: "pointer",
                          }}
                        >
                          {matrixItem.name}
                        </Typography>
                      </Tooltip>
                    </ListItem>
                  ))}
                </List>
              </Collapse>
            </Fragment>
          )
      )}
    </List>
  );
}

export default DataView;
