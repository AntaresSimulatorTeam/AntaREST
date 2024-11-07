/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useCallback, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Box, Divider } from "@mui/material";
import debug from "debug";
import { useTranslation } from "react-i18next";
import { usePromise as usePromiseWrapper } from "react-use";
import { StudyMetadata, VariantTree } from "../../../common/types";
import { getStudyMetadata } from "../../../services/api/study";
import NavHeader from "./NavHeader";
import {
  getVariantChildren,
  getVariantParents,
} from "../../../services/api/variant";
import TabWrapper from "./explore/TabWrapper";
import HomeView from "./HomeView";
import {
  fetchStudyVersions,
  setCurrentStudy,
} from "../../../redux/ducks/studies";
import { findNodeInTree } from "../../../services/utils";
import CommandDrawer from "./Commands";
import { addWsEventListener } from "../../../services/webSocket/ws";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import SimpleLoader from "../../common/loaders/SimpleLoader";
import FreezeStudy from "./FreezeStudy";
import { WsEvent } from "@/services/webSocket/types";
import { WsEventType } from "@/services/webSocket/constants";

const logError = debug("antares:singlestudy:error");

interface Props {
  isExplorer?: boolean;
}

function SingleStudy(props: Props) {
  const { isExplorer } = props;
  const { studyId } = useParams(); // TO DO
  const [t] = useTranslation();
  const [study, setStudy] = useState<StudyMetadata>();
  const [parent, setParent] = useState<StudyMetadata>();
  const [tree, setTree] = useState<VariantTree>();
  const [openCommands, setOpenCommands] = useState(false);
  const dispatch = useAppDispatch();
  const mounted = usePromiseWrapper();

  const tabList = useMemo(
    () => [
      {
        label: t("study.modelization"),
        path: `/studies/${studyId}/explore/modelization`,
      },
      {
        label: t("study.configuration"),
        path: `/studies/${studyId}/explore/configuration`,
      },
      {
        label: t("study.tableMode"),
        path: `/studies/${studyId}/explore/tablemode`,
      },
      { label: "Xpansion", path: `/studies/${studyId}/explore/xpansion` },
      {
        label: t("study.results"),
        path: `/studies/${studyId}/explore/results`,
      },
      {
        label: t("study.debug"),
        path: `/studies/${studyId}/explore/debug`,
      },
    ],
    [studyId, t],
  );

  const updateStudyData = useCallback(async () => {
    if (!studyId) {
      return;
    }
    try {
      const tmpStudy = await mounted(getStudyMetadata(studyId));
      if (tmpStudy) {
        const tmpParents = await mounted(getVariantParents(tmpStudy.id));
        let root: StudyMetadata = tmpStudy;
        if (tmpParents.length > 0) {
          root = tmpParents[tmpParents.length - 1];
        }
        const tmpTree = await mounted(getVariantChildren(root.id));
        setParent(tmpParents.length > 0 ? tmpParents[0] : undefined);
        setStudy(tmpStudy);
        setTree(tmpTree);
      }
    } catch (e) {
      logError("Failed to fetch study informations", study, e);
    }
  }, [studyId]);

  const listener = useCallback(
    (ev: WsEvent) => {
      switch (ev.type) {
        case WsEventType.StudyEdited:
          if (ev.payload.id === studyId) {
            updateStudyData();
          }
          break;

        default:
          break;
      }
    },
    [studyId, t, updateStudyData],
  );

  useEffect(() => {
    const init = async () => {
      if (studyId) {
        dispatch(setCurrentStudy(studyId));
        dispatch(fetchStudyVersions());
        updateStudyData();
      }
    };
    init();
  }, [studyId]);

  useEffect(() => {
    const title = document.querySelector("title");
    if (title && study) {
      title.textContent = `Antares Web | ${study.name} (${study.id})`;
    }
    return () => {
      if (title) {
        title.textContent = "Antares Web";
      }
    };
  }, [study]);

  useEffect(() => {
    return addWsEventListener(listener);
  }, [listener]);

  if (study === undefined) {
    return <SimpleLoader />;
  }

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
        updateStudyData={updateStudyData}
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
        position="relative"
      >
        {isExplorer === true ? (
          <TabWrapper study={study} border tabList={tabList} />
        ) : (
          <HomeView study={study} tree={tree} />
        )}
        <FreezeStudy studyId={studyId!} />
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

export default SingleStudy;
