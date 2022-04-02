/* eslint-disable react-hooks/exhaustive-deps */
<<<<<<< HEAD
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Divider } from "@mui/material";
import debug from "debug";
import { StudyMetadata, VariantTree } from "../../common/types";
import { getStudyMetadata } from "../../services/api/study";
import NavHeader from "../../components/singlestudy/NavHeader";
import {
  getVariantChildren,
  getVariantParents,
} from "../../services/api/variant";
import TabWrapper from "../../components/singlestudy/explore/TabWrapper";
import HomeView from "../../components/singlestudy/HomeView";
=======
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, Outlet } from 'react-router-dom';
import { Box, Button, Divider, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import debug from 'debug';
import { connect, ConnectedProps } from 'react-redux';
import { StudyMetadata, VariantTree } from '../../common/types';
import { getStudyMetadata } from '../../services/api/study';
import NavHeader from '../../components/singlestudy/NavHeader';
import { getDirectParent, getVariantChildren, getVariantParents } from '../../services/api/variant';
import TabWrapper from '../../components/singlestudy/explore/TabWrapper';
import HomeView from '../../components/singlestudy/HomeView';
import { viewStudy } from '../../store/study';
>>>>>>> Add a current study menu

const logError = debug("antares:singlestudy:error");

<<<<<<< HEAD
interface Props {
  isExplorer?: boolean;
=======
const mapState = () => ({});

const mapDispatch = ({
  setCurrentStudy: viewStudy,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
    isExplorer?: boolean
>>>>>>> Add a current study menu
}
type Props = PropsFromRedux & OwnProps;

function SingleStudy(props: Props) {
  const { studyId } = useParams();
<<<<<<< HEAD
=======
  const { setCurrentStudy } = props;
  const [t] = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
>>>>>>> Add a current study menu
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
        setCurrentStudy(studyId);
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

export default connector(SingleStudy);
