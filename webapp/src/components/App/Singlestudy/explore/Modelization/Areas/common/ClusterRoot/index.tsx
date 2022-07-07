import {
  Box,
  Button,
  List,
  ListSubheader,
  Collapse,
  ListItemText,
  IconButton,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import * as R from "ramda";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DeleteIcon from "@mui/icons-material/Delete";
import { Fragment, useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import {
  Header,
  ListContainer,
  Root,
  GroupButton,
  ClusterButton,
} from "./style";
import usePromise, {
  PromiseStatus,
} from "../../../../../../../../hooks/usePromise";
import SimpleLoader from "../../../../../../../common/loaders/SimpleLoader";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { Cluster, StudyMetadata } from "../../../../../../../../common/types";
import {
  getCurrentAreaId,
  getCurrentClusters,
} from "../../../../../../../../redux/selectors";
import { getStudyData } from "../../../../../../../../services/api/study";
import { Clusters, byGroup, ClusterElement } from "./utils";
import AddClusterDialog from "./AddClusterDialog";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { appendCommands } from "../../../../../../../../services/api/variant";
import { CommandEnum } from "../../../../../Commands/Edition/commandTypes";

interface Props {
  children: (elm: {
    cluster: Cluster["id"];
    groupList: Array<string>;
  }) => React.ReactNode;
  study: StudyMetadata;
  fixedGroupList: Array<string>;
  type: "thermals" | "renewables";
  backButtonName: string;
}

function ClusterRoot(props: Props) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const { study, type, fixedGroupList, backButtonName, children } = props;
  const currentArea = useAppSelector(getCurrentAreaId);
  const clusterInitList = useAppSelector((state) =>
    getCurrentClusters(type, study.id, state)
  );
  // TO DO: Replace this and Optimize to add/remove the right clusters
  const { data: clusterData, status } = usePromise(
    () =>
      getStudyData(
        study.id,
        `input/${
          type === "thermals" ? "thermal" : type
        }/clusters/${currentArea}/list`,
        3
      ),
    [study.id, currentArea, clusterInitList]
  );

  const clusters = useMemo(() => {
    const tmpData: Array<ClusterElement> = clusterData
      ? Object.keys(clusterData).map((item) => ({
          id: item,
          name: clusterData[item].name,
          group: clusterData[item].group ? clusterData[item].group : "*",
        }))
      : [];
    const clusterDataByGroup: Record<string, ClusterElement[]> =
      byGroup(tmpData);
    const clustersObj = Object.keys(clusterDataByGroup).map(
      (group) =>
        [group, { items: clusterDataByGroup[group], isOpen: true }] as Readonly<
          [
            string,
            {
              items: Array<ClusterElement>;
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
  const [currentCluster, setCurrentCluster] = useState<Cluster["id"]>();

  const clusterGroupList: Array<string> = useMemo(() => {
    const tab = [...new Set([...fixedGroupList, ...Object.keys(clusters)])];
    return tab;
  }, [clusters, fixedGroupList]);

  const handleToggleGroupOpen = (groupName: string): void => {
    setClusterList({
      ...clusterList,
      [groupName]: {
        items: clusterList[groupName].items,
        isOpen: !clusterList[groupName].isOpen,
      },
    });
  };

  const handleClusterDeletion = async (id: Cluster["id"]) => {
    try {
      const tmpData = { ...clusterData };
      delete tmpData[id];
      await appendCommands(study.id, [
        {
          action:
            type === "thermals"
              ? CommandEnum.REMOVE_CLUSTER
              : CommandEnum.REMOVE_RENEWABLES_CLUSTER,
          args: {
            area_id: currentArea,
            cluster_id: id,
          },
        },
      ]);
      enqueueSnackbar(t("study.success.deleteCluster"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.deleteCluster"), e as AxiosError);
    }
  };

  useEffect(() => {
    setClusterList({ ...clusters });
  }, [clusters]);

  useEffect(() => {
    setCurrentCluster(undefined);
  }, [currentArea]);

  return currentCluster === undefined ? (
    <Root>
      <Header>
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
              <List
                sx={{
                  width: "100%",
                  boxSizing: "border-box",
                }}
                // component="nav"
                aria-labelledby="nested-list-subheader"
                subheader={
                  <ListSubheader
                    component="div"
                    id="nested-list-subheader"
                    sx={{
                      color: "white",
                      bgcolor: "#0000",
                      fontSize: "18px",
                    }}
                  >
                    {t("study.modelization.clusters.byGroups")}
                  </ListSubheader>
                }
              >
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    width: "100%",
                    height: "100%",
                    overflowY: "auto",
                  }}
                >
                  {Object.keys(clusterList).map((group) => {
                    const clusterItems = clusterList[group];
                    const { items, isOpen } = clusterItems;
                    return (
                      <Fragment key={group}>
                        <GroupButton
                          onClick={() => handleToggleGroupOpen(group)}
                        >
                          <ListItemText
                            primary={
                              <Typography
                                sx={{
                                  color: "white",
                                  fontWeight: "bold",
                                  borderRadius: "4px",
                                }}
                              >
                                {group}
                              </Typography>
                            }
                          />
                          {isOpen ? (
                            <ExpandLessIcon color="primary" />
                          ) : (
                            <ExpandMoreIcon color="primary" />
                          )}
                        </GroupButton>
                        {items.map((item: ClusterElement) => (
                          <Collapse
                            key={item.id}
                            in={isOpen}
                            timeout="auto"
                            unmountOnExit
                          >
                            <List component="div" disablePadding>
                              <ClusterButton
                                onClick={() => setCurrentCluster(item.id)}
                              >
                                <ListItemText primary={item.name} />
                                <IconButton
                                  edge="end"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleClusterDeletion(item.id);
                                  }}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </ClusterButton>
                            </List>
                          </Collapse>
                        ))}
                      </Fragment>
                    );
                  })}
                </Box>
                {isAddClusterDialogOpen && (
                  <AddClusterDialog
                    open={isAddClusterDialogOpen}
                    title={t("study.modelization.clusters.newCluster")}
                    clusterGroupList={clusterGroupList}
                    clusterData={clusterData}
                    studyId={study.id}
                    area={currentArea}
                    type={type}
                    onCancel={() => setIsAddClusterDialogOpen(false)}
                  />
                )}
              </List>
            ),
          ],
        ])(status)}
      </ListContainer>
    </Root>
  ) : (
    <Root sx={{ p: 2 }}>
      <Header sx={{ justifyContent: "flex-start", mb: 3 }}>
        <Button
          variant="text"
          color="secondary"
          onClick={() => setCurrentCluster(undefined)}
          startIcon={<ArrowBackIcon />}
        >
          {backButtonName}
        </Button>
      </Header>
      <Box sx={{ width: "100%", flex: 1, overflowY: "auto" }}>
        {children({
          cluster: currentCluster,
          groupList: clusterGroupList,
        })}
      </Box>
    </Root>
  );
}

export default ClusterRoot;
