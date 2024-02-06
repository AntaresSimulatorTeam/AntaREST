import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Box,
  Typography,
  Breadcrumbs,
  Tooltip,
  IconButton,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import AutoSizer from "react-virtualized-auto-sizer";
import HomeIcon from "@mui/icons-material/Home";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import FolderOffIcon from "@mui/icons-material/FolderOff";
import RadarIcon from "@mui/icons-material/Radar";
import { FixedSizeGrid, GridOnScrollProps } from "react-window";
import { AxiosError } from "axios";
import { StudyMetadata } from "../../../../common/types";
import { STUDIES_HEIGHT_HEADER, STUDIES_LIST_HEADER_HEIGHT } from "../../theme";
import {
  setStudyScrollPosition,
  updateStudiesSortConf,
  updateStudyFilters,
} from "../../../../redux/ducks/studies";
import LauncherDialog from "../LauncherDialog";
import useDebounce from "../../../../hooks/useDebounce";
import {
  getStudiesScrollPosition,
  getStudiesSortConf,
  getStudyFilters,
} from "../../../../redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import StudyCardCell from "./StudyCardCell";
import BatchModeMenu from "../BatchModeMenu";
import RefreshButton from "../RefreshButton";
import { scanFolder } from "../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import SelectFE from "../../../common/fieldEditors/SelectFE";

const CARD_TARGET_WIDTH = 500;
const CARD_HEIGHT = 250;

export interface StudiesListProps {
  studyIds: Array<StudyMetadata["id"]>;
}

function StudiesList(props: StudiesListProps) {
  const { studyIds } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [studyToLaunch, setStudyToLaunch] = useState<
    StudyMetadata["id"] | null
  >(null);
  const scrollPosition = useAppSelector(getStudiesScrollPosition);
  const sortConf = useAppSelector(getStudiesSortConf);
  const folder = useAppSelector((state) => getStudyFilters(state).folder);
  const strictFolderFilter = useAppSelector(
    (state) => getStudyFilters(state).strictFolder,
  );
  const [folderList, setFolderList] = useState(folder.split("/"));
  const dispatch = useAppDispatch();
  const [selectedStudies, setSelectedStudies] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [confirmFolderScan, setConfirmFolderScan] = useState<boolean>(false);

  useEffect(() => {
    setFolderList(folder.split("/"));
  }, [folder]);

  useEffect(() => {
    if (!selectionMode) {
      setSelectedStudies([]);
    }
  }, [selectionMode]);

  useEffect(() => {
    if (selectedStudies.length === 0) {
      setSelectionMode(false);
    }
  }, [selectedStudies]);

  const sortOptions = useMemo(
    () => [
      {
        label: t("studies.sortByName"),
        value: JSON.stringify({ property: "name", order: "ascend" }),
        icon: ArrowUpwardIcon,
      },
      {
        label: t("studies.sortByName"),
        value: JSON.stringify({ property: "name", order: "descend" }),
        icon: ArrowDownwardIcon,
      },
      {
        label: t("studies.sortByDate"),
        value: JSON.stringify({
          property: "modificationDate",
          order: "ascend",
        }),
        icon: ArrowUpwardIcon,
      },
      {
        label: t("studies.sortByDate"),
        value: JSON.stringify({
          property: "modificationDate",
          order: "descend",
        }),
        icon: ArrowDownwardIcon,
      },
    ],
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleScroll = useDebounce(
    (scrollProp: GridOnScrollProps) => {
      dispatch(setStudyScrollPosition(scrollProp.scrollTop));
    },
    { wait: 400, trailing: true },
  );

  const handleToggleSelectStudy = useCallback((sid: string) => {
    setSelectedStudies((prevState) => {
      const newSelectedStudies = prevState.filter((s) => s !== sid);
      if (newSelectedStudies.length !== prevState.length) {
        return newSelectedStudies;
      }
      return newSelectedStudies.concat([sid]);
    });
  }, []);

  const handleFolderScan = async (): Promise<void> => {
    try {
      // Remove "/root" from the path
      const folder = folderList.slice(1).join("/");
      await scanFolder(folder);
      setConfirmFolderScan(false);
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.scanFolder"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const setFolder = (value: string) => {
    dispatch(updateStudyFilters({ folder: value }));
  };

  const toggleStrictFolder = useCallback(() => {
    dispatch(updateStudyFilters({ strictFolder: !strictFolderFilter }));
  }, [dispatch, strictFolderFilter]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      height={`calc(100vh - ${STUDIES_HEIGHT_HEADER}px)`}
      flex={1}
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      sx={{ overflowX: "hidden", overflowY: "hidden" }}
    >
      <Box
        width="100%"
        height={`${STUDIES_LIST_HEADER_HEIGHT}px`}
        px={2}
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
        boxSizing="border-box"
      >
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <Breadcrumbs
            separator={<NavigateNextIcon fontSize="small" />}
            aria-label="breadcrumb"
          >
            {folderList.map((fol, index) => {
              const path = folderList.slice(0, index + 1).join("/");
              if (index === 0) {
                return (
                  <HomeIcon
                    key={path}
                    sx={{
                      color: "text.primary",
                      cursor: "pointer",
                      "&:hover": {
                        color: "primary.main",
                      },
                    }}
                    onClick={() => setFolder("root")}
                  />
                );
              }
              return (
                <Typography
                  key={path}
                  sx={{
                    color: "text.primary",
                    cursor: "pointer",
                    "&:hover": {
                      textDecoration: "underline",
                      color: "primary.main",
                    },
                  }}
                  onClick={() => setFolder(path)}
                >
                  {fol}
                </Typography>
              );
            })}
          </Breadcrumbs>
          <Typography mx={2}>
            ({`${studyIds.length} ${t("global.studies").toLowerCase()}`})
          </Typography>
          <Tooltip title={t("studies.filters.strictfolder") as string}>
            <IconButton onClick={toggleStrictFolder}>
              <FolderOffIcon
                color={strictFolderFilter ? "secondary" : "disabled"}
              />
            </IconButton>
          </Tooltip>
          {folder !== "root" && (
            <Tooltip title={t("studies.scanFolder") as string}>
              <IconButton onClick={() => setConfirmFolderScan(true)}>
                <RadarIcon />
              </IconButton>
            </Tooltip>
          )}
          {folder !== "root" && confirmFolderScan && (
            <ConfirmationDialog
              titleIcon={RadarIcon}
              onCancel={() => setConfirmFolderScan(false)}
              onConfirm={handleFolderScan}
              alert="warning"
              open
            >
              {`${t("studies.scanFolder")} ${folder}?`}
            </ConfirmationDialog>
          )}
        </Box>
        <Box
          display="flex"
          flexDirection="row"
          justifyContent="center"
          alignItems="center"
          boxSizing="border-box"
        >
          <BatchModeMenu
            selectedIds={selectedStudies}
            selectionMode={selectionMode}
            setSelectionMode={setSelectionMode}
          />
          <RefreshButton />
          <SelectFE
            label={t("studies.sortBy")}
            value={JSON.stringify(sortConf)}
            onChange={(e) =>
              dispatch(
                updateStudiesSortConf(JSON.parse(e.target.value as string)),
              )
            }
            options={sortOptions}
          />
        </Box>
      </Box>
      <Box sx={{ width: 1, height: 1 }}>
        <AutoSizer>
          {({ height, width }) => {
            const paddedWidth = width - 10;
            const columnWidth =
              paddedWidth /
              Math.max(Math.floor(paddedWidth / CARD_TARGET_WIDTH), 1);
            const columnCount = Math.floor(paddedWidth / columnWidth);
            const rowHeight = CARD_HEIGHT;

            return (
              <FixedSizeGrid
                key={studyIds.join()}
                columnCount={columnCount}
                columnWidth={columnWidth}
                height={height}
                width={width}
                rowCount={Math.ceil(studyIds.length / columnCount)}
                rowHeight={rowHeight}
                initialScrollTop={scrollPosition}
                onScroll={handleScroll}
                useIsScrolling
                itemData={{
                  studyIds,
                  setStudyToLaunch,
                  columnCount,
                  columnWidth,
                  rowHeight,
                  selectedStudies,
                  toggleSelect: handleToggleSelectStudy,
                  selectionMode,
                }}
              >
                {StudyCardCell}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </Box>
      {studyToLaunch && (
        <LauncherDialog
          open
          studyIds={[studyToLaunch]}
          onClose={() => setStudyToLaunch(null)}
        />
      )}
    </Box>
  );
}

export default StudiesList;
