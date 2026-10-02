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

import SimpleLoader from "@/components/loaders/SimpleLoader";
import { directoryQueries } from "@/queries/directories/queries";
import { variantQueries } from "@/queries/variants/queries";
import { setCurrentStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesError, getStudiesStatus, getStudy } from "@/redux/selectors";
import { appendColon } from "@/utils/i18nUtils";
import { Box, Stack } from "@mui/material";
import { createFileRoute, Outlet } from "@tanstack/react-router";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import FreezeStudy from "./-components/FreezeStudy";
import NavHeader from "./-components/NavHeader";

export const Route = createFileRoute("/_authenticated/studies/$studyId")({
  loader: async ({ context, params: { studyId } }) => {
    // Used in the Breadcrumb of the NavHeader
    await context.queryClient.ensureQueryData(directoryQueries.list());
    await context.queryClient.ensureQueryData(variantQueries.variantTree(studyId));
  },
  component: StudyHomeLayout,
});

function StudyHomeLayout() {
  const { studyId } = Route.useParams();
  const dispatch = useAppDispatch();
  const studiesStatus = useAppSelector(getStudiesStatus);
  const studiesError = useAppSelector(getStudiesError);
  const study = useAppSelector((state) => getStudy(state, studyId));
  const { t } = useTranslation();

  useEffect(() => {
    dispatch(setCurrentStudy(studyId));
  }, [dispatch, studyId]);

  // Change the name of the web browser tab
  useEffect(() => {
    if (!study) {
      return;
    }

    document.title = `Antares Web | ${study.name} (${study.id})`;

    return () => {
      document.title = "Antares Web";
    };
  }, [study]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Status must be "succeeded" to ensure that the study is loaded in the Redux store
  if (studiesStatus === "idle" || studiesStatus === "loading") {
    return <SimpleLoader />;
  }

  if (studiesStatus === "failed") {
    throw new Error(`${appendColon(t("studies.error.loadStudies"))} ${studiesError}`);
  }

  return (
    <Stack direction="column" sx={{ position: "relative", overflow: "auto", height: 1, width: 1 }}>
      <NavHeader />
      <Box sx={{ overflow: "auto", height: 1, width: 1 }}>
        <Outlet />
      </Box>
      <FreezeStudy />
    </Stack>
  );
}
