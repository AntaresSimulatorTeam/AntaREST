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

/* eslint-disable react-hooks/exhaustive-deps */
import AddIcon from "@mui/icons-material/Add";
import { Box, Button } from "@mui/material";
import type { AxiosError } from "axios";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import {
  createXpansionConfiguration,
  xpansionConfigurationExist,
} from "../../../../../services/api/xpansion";
import type { StudyMetadata } from "../../../../../types/types";
import UsePromiseCond from "../../../../common/utils/UsePromiseCond";
import TabWrapper from "../TabWrapper";

function Xpansion() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [exist, setExist] = useState<boolean>(false);

  const res = usePromiseWithSnackbarError(() => xpansionConfigurationExist(study.id), {
    errorMessage: t("xpansion.error.loadConfiguration"),
    deps: [exist],
  });

  const tabList = useMemo(
    () => [
      {
        label: t("xpansion.candidates"),
        path: `/studies/${study?.id}/explore/xpansion/candidates`,
      },
      {
        label: t("global.settings"),
        path: `/studies/${study?.id}/explore/xpansion/settings`,
      },
      {
        label: t("xpansion.constraints"),
        path: `/studies/${study?.id}/explore/xpansion/constraints`,
      },
      {
        label: t("xpansion.weights"),
        path: `/studies/${study?.id}/explore/xpansion/weights`,
      },
      {
        label: t("xpansion.capacities"),
        path: `/studies/${study?.id}/explore/xpansion/capacities`,
      },
    ],
    [study],
  );

  useEffect(() => {
    if (window.history.state.usr) {
      setExist(window.history.state.usr.exist);
    } else {
      setExist(!!res.data);
    }
  }, [window.history.state.usr, res.data]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const createXpansion = async () => {
    try {
      if (study) {
        await createXpansionConfiguration(study.id);
      }
    } catch (e) {
      enqueueErrorSnackbar(t("xpansion.error.createConfiguration"), e as AxiosError);
    } finally {
      setExist(true);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <UsePromiseCond
        response={res}
        ifFulfilled={(data) =>
          !data && !exist ? (
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
            <TabWrapper study={study} tabList={tabList} disablePadding />
          )
        }
      />
    </>
  );
}

export default Xpansion;
