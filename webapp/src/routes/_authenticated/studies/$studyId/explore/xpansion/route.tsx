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

import TabsView from "@/components/page/TabsView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import AddIcon from "@mui/icons-material/Add";
import { Box, Button } from "@mui/material";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import {
  createXpansionConfiguration,
  xpansionConfigurationExist,
} from "../../../../../../services/api/xpansion";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/xpansion")({
  validateSearch: (search) => ({
    reload: typeof search.reload === "number" ? search.reload : undefined,
  }),

  component: XpansionLayout,
});

function XpansionLayout() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const navigate = Route.useNavigate();
  const params = Route.useParams();
  const search = Route.useSearch();
  const { studyId } = params;

  const response = usePromiseWithSnackbarError(() => xpansionConfigurationExist(studyId), {
    errorMessage: t("xpansion.error.loadConfiguration"),
    deps: [studyId, search.reload],
  });

  useEffect(() => {
    if (search.reload) {
      navigate({
        search: { reload: undefined },
      });
    }
  }, [navigate, search.reload]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const createXpansion = async () => {
    try {
      await createXpansionConfiguration(studyId);
      response.reload();
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.createConfiguration"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <UsePromiseCond
        response={response}
        ifFulfilled={(isConfigExist) =>
          !isConfigExist ? (
            <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
              <Button
                color="primary"
                variant="contained"
                startIcon={<AddIcon />}
                onClick={createXpansion}
              >
                {t("xpansion.newXpansionConfig")}
              </Button>
            </Box>
          ) : (
            <TabsView
              tabs={[
                {
                  id: "candidates",
                  label: t("xpansion.candidates"),
                  linkOptions: linkOptions({
                    to: "/studies/$studyId/explore/xpansion/candidates",
                    params,
                    search,
                  }),
                },
                {
                  id: "settings",
                  label: t("global.settings"),
                  linkOptions: linkOptions({
                    to: "/studies/$studyId/explore/xpansion/settings",
                    params,
                    search,
                  }),
                },
                {
                  id: "constraints",
                  label: t("xpansion.constraints"),
                  linkOptions: linkOptions({
                    to: "/studies/$studyId/explore/xpansion/constraints",
                    params,
                    search,
                  }),
                },
                {
                  id: "weights",
                  label: t("xpansion.weights"),
                  linkOptions: linkOptions({
                    to: "/studies/$studyId/explore/xpansion/weights",
                    params,
                    search,
                  }),
                },
                {
                  id: "capacities",
                  label: t("xpansion.capacities"),
                  linkOptions: linkOptions({
                    to: "/studies/$studyId/explore/xpansion/capacities",
                    params,
                    search,
                  }),
                },
              ]}
            />
          )
        }
      />
    </>
  );
}
