/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import { Box, Divider } from "@mui/material";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { fetchStudyVersions, setCurrentStudy } from "../../../redux/ducks/studies";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { getStudyMetadata } from "../../../services/api/study";
import { getVariantParents, getVariantTree } from "../../../services/api/variant";
import { addWsEventListener } from "../../../services/webSocket/ws";
import TabWrapper from "./explore/TabWrapper";
import FreezeStudy from "./FreezeStudy";
import HomeView from "./HomeView";
import NavHeader from "./NavHeader";

interface Props {
  isExplorer?: boolean;
}

function SingleStudy({ isExplorer }: Props) {
  const { studyId } = useParams();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();

  const res = usePromise(async () => {
    if (!studyId) {
      throw new Error("No study ID provided");
    }

    const study = await getStudyMetadata(studyId);

    const parents = await getVariantParents(studyId);
    const parentStudy = parents.length > 0 ? parents[0] : undefined;

    const root = parents.length > 0 ? parents.at(-1) : study;
    const variantTree = root ? await getVariantTree(root.id) : undefined;

    return { study, parentStudy, variantTree };
  }, [studyId]);

  useEffect(() => {
    if (studyId) {
      dispatch(setCurrentStudy(studyId));
      dispatch(fetchStudyVersions());
    }
  }, [dispatch, studyId]);

  // Change the name of the web browser tab
  useEffect(() => {
    const study = res.data?.study;

    if (!study) {
      return;
    }

    document.title = `Antares Web | ${study.name} (${study.id})`;

    return () => {
      document.title = "Antares Web";
    };
  }, [res.data?.study]);

  // Reload the study when it is edited
  useEffect(() => {
    const listener = (event: WsEvent) => {
      if (event.type === WsEventType.StudyEdited || event.type === WsEventType.StudyDataEdited) {
        if (event.payload.id === studyId) {
          res.reload();
        }
      }
    };

    return addWsEventListener(listener);
  }, [res, studyId]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      keepLastResolvedOnReload
      ifFulfilled={({ study, parentStudy, variantTree }) => (
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
            parentStudy={parentStudy}
            isExplorer={isExplorer}
            variantTree={variantTree}
          />
          {!isExplorer && <Divider flexItem />}
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
              <TabWrapper
                study={study}
                divider
                tabList={[
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
                ]}
                disablePadding
              />
            ) : (
              <HomeView study={study} variantTree={variantTree} />
            )}
            <FreezeStudy studyId={study.id} />
          </Box>
        </Box>
      )}
    />
  );
}

export default SingleStudy;
