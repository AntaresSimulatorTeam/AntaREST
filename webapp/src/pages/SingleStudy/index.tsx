/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useCallback, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Divider } from "@mui/material";
import debug from "debug";
import { useTranslation } from "react-i18next";
import {
  StudyMetadata,
  StudySummary,
  VariantTree,
  WSEvent,
  WSMessage,
} from "../../common/types";
import { getStudyMetadata } from "../../services/api/study";
import NavHeader from "../../components/singlestudy/NavHeader";
import {
  getVariantChildren,
  getVariantParents,
} from "../../services/api/variant";
import TabWrapper from "../../components/singlestudy/explore/TabWrapper";
import HomeView from "../../components/singlestudy/HomeView";
import { setCurrentStudy } from "../../redux/ducks/studies";
import { findNodeInTree } from "../../services/utils";
import CommandDrawer from "../../components/singlestudy/Commands";
import { addWsMessageListener } from "../../services/webSockets";
import { useAppDispatch } from "../../redux/hooks";

const logError = debug("antares:singlestudy:error");

interface Props {
  isExplorer?: boolean;
}

function SingleStudy(props: Props) {
  const { isExplorer } = props;
  const { studyId } = useParams();
  const [t] = useTranslation();
  const [study, setStudy] = useState<StudyMetadata>();
  const [parent, setParent] = useState<StudyMetadata>();
  const [tree, setTree] = useState<VariantTree>();
  const [openCommands, setOpenCommands] = useState(false);
  const dispatch = useAppDispatch();

  const tabList = useMemo(
    () => [
      {
        label: t("singlestudy:modelization"),
        path: `/studies/${studyId}/explore/modelization`,
      },
      {
        label: t("singlestudy:configuration"),
        path: `/studies/${studyId}/explore/configuration`,
      },
      { label: "Xpansion", path: `/studies/${studyId}/explore/xpansion` },
      {
        label: t("singlestudy:results"),
        path: `/studies/${studyId}/explore/results`,
      },
    ],
    [studyId]
  );

  const updateStudyData = useCallback(async () => {
    if (!studyId) return;
    try {
      const tmpStudy = await getStudyMetadata(studyId);
      if (tmpStudy) {
        const tmpParents = await getVariantParents(tmpStudy.id);
        let root: StudyMetadata = tmpStudy;
        if (tmpParents.length > 0) root = tmpParents[tmpParents.length - 1];
        const tmpTree = await getVariantChildren(root.id);
        setParent(tmpParents.length > 0 ? tmpParents[0] : undefined);
        setStudy(tmpStudy);
        setTree(tmpTree);
      }
    } catch (e) {
      logError("Failed to fetch study informations", study, e);
    }
  }, [studyId]);

  const listener = useCallback(
    async (ev: WSMessage) => {
      const studySummary = ev.payload as StudySummary;
      switch (ev.type) {
        case WSEvent.STUDY_EDITED:
          if (studySummary.id === studyId) {
            updateStudyData();
          }
          break;

        default:
          break;
      }
    },
    [studyId, t, updateStudyData]
  );

  useEffect(() => {
    const init = async () => {
      if (studyId) {
        dispatch(setCurrentStudy(studyId));
        updateStudyData();
      }
    };
    init();
  }, [studyId]);

  useEffect(() => {
    return addWsMessageListener(listener);
  }, [listener]);

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
    >
      <NavHeader
        study={study}
        parent={parent}
        isExplorer={isExplorer}
        openCommands={() => setOpenCommands(true)}
        childrenTree={
          study !== undefined && tree !== undefined
            ? findNodeInTree(study.id, tree)
            : undefined
        }
      />
      {!isExplorer && <Divider sx={{ width: "98%" }} />}
      <Box
        width="100%"
        flex={1}
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
        boxSizing="border-box"
        overflow="hidden"
      >
        {isExplorer === true ? (
          <TabWrapper study={study} border tabList={tabList} />
        ) : (
          <HomeView study={study} tree={tree} />
        )}
      </Box>
      {openCommands && studyId && (
        <CommandDrawer
          open={openCommands}
          studyId={studyId}
          onClose={() => setOpenCommands(false)}
        />
      )}
    </Box>
  );
}

SingleStudy.defaultProps = {
  isExplorer: undefined,
};

export default SingleStudy;
