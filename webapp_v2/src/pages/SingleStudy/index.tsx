/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Outlet } from "react-router-dom";
import { Box, Button, Divider, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import debug from "debug";
import { StudyMetadata, VariantTree } from "../../common/types";
import { getStudyMetadata } from "../../services/api/study";
import NavHeader from "../../components/singlestudy/NavHeader";
import {
  getDirectParent,
  getVariantChildren,
  getVariantParents,
} from "../../services/api/variant";
import TabWrapper from "../../components/singlestudy/explore/TabWrapper";
import HomeView from "../../components/singlestudy/HomeView";

const logError = debug("antares:singlestudy:error");

interface Props {
  isExplorer?: boolean;
}

function SingleStudy(props: Props) {
  const { studyId } = useParams();
  const [t] = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { isExplorer } = props;

  const [study, setStudy] = useState<StudyMetadata>();
  const [parents, setParents] = useState<Array<StudyMetadata>>([]);
  const [childrenTree, setChildren] = useState<VariantTree>();

  const tabList = useMemo(
    () => [
      {
        label: "Modelization",
        path: `/studies/${studyId}/explore/modelization`,
      },
      {
        label: "Configuration",
        path: `/studies/${studyId}/explore/configuration`,
      },
      { label: "Results", path: `/studies/${studyId}/explore/results` },
    ],
    [studyId]
  );

  useEffect(() => {
    const init = async () => {
      if (studyId) {
        try {
          const tmpStudy = await getStudyMetadata(studyId, false);
          if (tmpStudy) {
            const tmpParents = await getVariantParents(tmpStudy.id);
            const childrenTree = await getVariantChildren(tmpStudy.id);
            setStudy(tmpStudy);
            setParents(tmpParents);
            setChildren(childrenTree);
          }
        } catch (e) {
          logError("Failed to fetch study informations", study, e);
        }
      }
    };
    init();
  }, [studyId]);

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
        parent={parents.length > 0 ? parents[0] : undefined}
        isExplorer={isExplorer}
        childrenTree={childrenTree}
      />
      {!isExplorer && <Divider sx={{ width: "98%" }} />}
      <Box
        width="100%"
        flexGrow={1}
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
          <HomeView
            study={study}
            parents={parents}
            childrenTree={childrenTree}
          />
        )}
      </Box>
    </Box>
  );
}

SingleStudy.defaultProps = {
  isExplorer: undefined,
};

export default SingleStudy;
