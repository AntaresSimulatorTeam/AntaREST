/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import ErrorView from "@/components/page/ErrorView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromise from "@/hooks/usePromise";
import { directoryQueries } from "@/queries/directories/queries";
import { setCurrentStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { getStudyMetadata } from "@/services/api/study";
import { getVariantParents, getVariantTree } from "@/services/api/variant";
import { countDescendants, findNodeInTree } from "@/services/utils";
import { WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import { addWsEventListener } from "@/services/webSocket/ws";
import { toError } from "@/utils/fnUtils";
import { Box, Divider } from "@mui/material";
import { createFileRoute, Outlet, useMatch } from "@tanstack/react-router";
import { isAxiosError } from "axios";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import FreezeStudy from "./-components/FreezeStudy";
import NavHeader from "./-components/NavHeader";

export const Route = createFileRoute("/_authenticated/studies/$studyId")({
  component: StudyHomeLayout,
  loader: ({ context }) => {
    return context.queryClient.ensureQueryData(directoryQueries.list());
  },
});

function StudyHomeLayout() {
  const { studyId } = Route.useParams();
  const dispatch = useAppDispatch();
  const match = useMatch({ from: "/_authenticated/studies/$studyId/explore", shouldThrow: false });
  const { t } = useTranslation();
  const isExplorer = !!match;

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
    dispatch(setCurrentStudy(studyId));
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
            <Outlet />
            <FreezeStudy studyId={study.id} />
          </Box>
        </Box>
      )}
      ifRejected={(err) => {
        const is404 = isAxiosError(err) && err.response?.status === 404;
        return <ErrorView error={is404 ? t("study.notFound", { id: studyId }) : toError(err)} />;
      }}
    />
  );
}
