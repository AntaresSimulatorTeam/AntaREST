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

import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { fetchStudyVersions, setCurrentStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { getStudyMetadata } from "@/services/api/study";
import { getVariantParents, getVariantTree } from "@/services/api/variant";
import { countDescendants, findNodeInTree } from "@/services/utils";
import { WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import { addWsEventListener } from "@/services/webSocket/ws";
import { Box, Divider } from "@mui/material";
import { createFileRoute, Outlet } from "@tanstack/react-router";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import FreezeStudy from "./-components/FreezeStudy";
import NavHeader from "./-components/NavHeader";
import { Route as StudyRootRoute } from "./index";

export const Route = createFileRoute("/_authenticated/studies/$studyId")({
  component: StudyLayout,
});

function StudyLayout() {
  const { studyId } = Route.useParams();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const isExplorer = !!StudyRootRoute.useMatch();

  const res = usePromise(async () => {
    const study = await getStudyMetadata(studyId);

    const parents = await getVariantParents(studyId);
    const parentStudy = parents.length > 0 ? parents[0] : undefined;

    const root = parents.length > 0 ? parents[parents.length - 1] : study;
    const variantTree = await getVariantTree(root.id);

    const tree = findNodeInTree(study.id, variantTree);
    const variantNb = tree ? countDescendants(tree) : 0;

    return { study, parentStudy, variantNb };
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
      ifFulfilled={({ study, parentStudy, variantNb }) => (
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
            variantNb={variantNb}
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
            {/* {isExplorer === true ? (
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
            )} */}
            <Outlet />
            <FreezeStudy studyId={study.id} />
          </Box>
        </Box>
      )}
    />
  );
}
