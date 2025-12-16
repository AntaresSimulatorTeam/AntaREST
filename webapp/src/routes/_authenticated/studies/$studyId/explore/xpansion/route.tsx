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
import { createFileRoute } from "@tanstack/react-router";
import type { AxiosError } from "axios";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";
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
  const study = useStudy();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { reload } = Route.useSearch();
  const navigate = Route.useNavigate();

  const response = usePromiseWithSnackbarError(() => xpansionConfigurationExist(study.id), {
    errorMessage: t("xpansion.error.loadConfiguration"),
    deps: [study.id, reload],
  });

  useEffect(() => {
    if (reload) {
      navigate({
        search: { reload: undefined },
      });
    }
  }, [navigate, reload]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const createXpansion = async () => {
    try {
      await createXpansionConfiguration(study.id);
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
                  linkOptions: {
                    to: "/studies/$studyId/explore/xpansion/candidates",
                    params: { studyId: study.id },
                  },
                },
                {
                  id: "settings",
                  label: t("global.settings"),
                  linkOptions: {
                    to: "/studies/$studyId/explore/xpansion/settings",
                    params: { studyId: study.id },
                  },
                },
                {
                  id: "constraints",
                  label: t("xpansion.constraints"),
                  linkOptions: {
                    to: "/studies/$studyId/explore/xpansion/constraints",
                    params: { studyId: study.id },
                  },
                },
                {
                  id: "weights",
                  label: t("xpansion.weights"),
                  linkOptions: {
                    to: "/studies/$studyId/explore/xpansion/weights",
                    params: { studyId: study.id },
                  },
                },
                {
                  id: "capacities",
                  label: t("xpansion.capacities"),
                  linkOptions: {
                    to: "/studies/$studyId/explore/xpansion/capacities",
                    params: { studyId: study.id },
                  },
                },
              ]}
            />
          )
        }
      />
    </>
  );
}
