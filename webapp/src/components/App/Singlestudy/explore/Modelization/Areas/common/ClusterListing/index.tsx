import SearchIcon from "@mui/icons-material/Search";
import {
  InputAdornment,
  TextField,
  Box,
  Button,
  List,
  ListSubheader,
  Collapse,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import * as R from "ramda";
import { useOutletContext } from "react-router";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DeleteIcon from "@mui/icons-material/Delete";
import ArrowForwardRoundedIcon from "@mui/icons-material/ArrowForwardRounded";
import { Fragment, useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { Header, ListContainer, Root } from "./style";
import usePromise, {
  PromiseStatus,
} from "../../../../../../../../hooks/usePromise";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { StudyMetadata } from "../../../../../../../../common/types";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import {
  editStudy,
  getStudyData,
} from "../../../../../../../../services/api/study";
import { Clusters, byGroup, Cluster, ClusterList } from "./utils";
import AddClusterDialog from "./AddClusterDialog";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";

interface Props {
  fixedGroupList: Array<string>;
}

function ClusterListing(props: Props) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const { fixedGroupList } = props;
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  console.log("CURRENT AREA: ", currentArea);
  const { data: clusterInitData, status } = usePromise(
    () =>
      getStudyData(study.id, `input/thermal/clusters/${currentArea}/list`, 3),
    [study.id, currentArea]
  );

  const [clusterData, setClusterData] = useState<ClusterList>(clusterInitData);
  const clusters = useMemo(() => {
    const clusterDataList: Record<string, Cluster[]> = byGroup(
      clusterData ? Object.values(clusterData) : []
    );
    const clustersObj = Object.keys(clusterDataList).map(
      (group) =>
        [group, { items: clusterDataList[group], isOpen: false }] as Readonly<
          [
            string,
            {
              items: Array<Cluster>;
              isOpen: boolean;
            }
          ]
        >
    );
    const clusterListObj: Clusters = R.fromPairs(clustersObj);
    return clusterListObj;
  }, [clusterData]);

  const [clusterList, setClusterList] = useState<Clusters>(clusters);
  const [isAddClusterDialogOpen, setIsAddClusterDialogOpen] = useState(false);

  const handleSearchFilterChange = (value: string): void => {
    console.log("FILTER: ", value);
  };

  const handleToggleGroupOpen = (groupName: string): void => {
    setClusterList({
      ...clusterList,
      [groupName]: {
        items: clusterList[groupName].items,
        isOpen: !clusterList[groupName].isOpen,
      },
    });
  };

  const handleClusterDeletion = async (name: string) => {
    const tmpData = { ...clusterData };
    delete tmpData[name];
    try {
      await editStudy(
        tmpData,
        study.id,
        `input/thermal/clusters/${currentArea}/list`
      );
      setClusterData(tmpData);
      enqueueSnackbar(t("study.success.deleteCluster"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.deleteCluster"), e as AxiosError);
    }
  };

  useEffect(() => {
    setClusterList({ ...clusters });
  }, [clusters]);

  useEffect(() => {
    setClusterData({ ...clusterInitData });
  }, [clusterInitData]);

  return (
    <Root>
      <Header>
        <TextField
          label={t("global.search")}
          variant="outlined"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          onChange={(e) => handleSearchFilterChange(e.target.value as string)}
        />
        <Button
          color="primary"
          variant="text"
          onClick={() => setIsAddClusterDialogOpen(true)}
        >
          {t("study.modelization.clusters.addCluster")}
        </Button>
      </Header>
      <ListContainer>
        {R.cond([
          [R.equals(PromiseStatus.Pending), () => <SimpleLoader />],
          [
            R.equals(PromiseStatus.Resolved),
            () => (
              <Box width="100%" height="100%">
                <List
                  sx={{
                    width: "100%",
                  }}
                  component="nav"
                  aria-labelledby="nested-list-subheader"
                  subheader={
                    <ListSubheader
                      component="div"
                      id="nested-list-subheader"
                      sx={{
                        color: "white",
                        bgcolor: "#0000",
                        fontSize: "16px",
                      }}
                    >
                      {t("study.modelization.clusters.byGroups")}
                    </ListSubheader>
                  }
                >
                  {Object.keys(clusterList).map((group) => {
                    const clusterItems = clusterList[group];
                    const { items, isOpen } = clusterItems;
                    return (
                      <Fragment key={group}>
                        <ListItemButton
                          onClick={() => handleToggleGroupOpen(group)}
                          sx={{
                            width: "100%",
                            mb: 1,
                          }}
                        >
                          <ListItemIcon>
                            <ArrowForwardRoundedIcon color="primary" />
                          </ListItemIcon>
                          <ListItemText
                            primary={group}
                            sx={{
                              color: "white",
                              fontWeight: "bold",
                              borderRadius: "4px",
                            }}
                          />
                          {isOpen ? (
                            <ExpandLessIcon color="primary" />
                          ) : (
                            <ExpandMoreIcon color="primary" />
                          )}
                        </ListItemButton>
                        {items.map((item: Cluster) => (
                          <Collapse
                            key={item.name}
                            in={isOpen}
                            timeout="auto"
                            unmountOnExit
                          >
                            <List component="div" disablePadding>
                              <ListItemButton sx={{ pl: 4 }}>
                                <ListItemText primary={item.name} />
                                <IconButton
                                  edge="end"
                                  onClick={() =>
                                    handleClusterDeletion(item.name)
                                  }
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </ListItemButton>
                            </List>
                          </Collapse>
                        ))}
                      </Fragment>
                    );
                  })}
                </List>
                {isAddClusterDialogOpen && (
                  <AddClusterDialog
                    open={isAddClusterDialogOpen}
                    title={t("study.modelization.clusters.newCluster")}
                    clusterGroupList={fixedGroupList.concat(
                      Object.keys(clusterList)
                    )}
                    clusterData={clusterData}
                    studyId={study.id}
                    area={currentArea}
                    onCancel={() => setIsAddClusterDialogOpen(false)}
                  />
                )}
              </Box>
            ),
          ],
        ])(status)}
      </ListContainer>
    </Root>
  );
}

export default ClusterListing;
