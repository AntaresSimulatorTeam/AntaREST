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

import ViewWrapper from "@/components/common/page/ViewWrapper";
import { copyStudy } from "@/services/api/studies";
import { Box, Button, Divider } from "@mui/material";
import type { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import { unarchiveStudy as callUnarchiveStudy } from "../../../../../services/api/study";
import type { StudyMetadata, VariantTree } from "../../../../../types/types";
import LaunchStudyDialog from "../../../shared/studies/dialogs/LaunchStudyDialog";
import CreateVariantDialog from "./CreateVariantDialog";
import LauncherHistory from "./LauncherHistory";
import Notes from "./Notes";

interface Props {
  study: StudyMetadata;
  variantTree: VariantTree;
}

function InformationView({ study, variantTree }: Props) {
  const navigate = useNavigate();
  const [t] = useTranslation();
  const [openVariantModal, setOpenVariantModal] = useState<boolean>(false);
  const [openLauncherModal, setOpenLauncherModal] = useState<boolean>(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const importStudy = async (study: StudyMetadata) => {
    try {
      await copyStudy({
        studyId: study.id,
        studyName: `${study.name} (${t("studies.copySuffix")})`,
        withOutputs: false,
      });
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.copyStudy"), e as AxiosError);
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.unarchive", { studyname: study.name }),
        e as AxiosError,
      );
    }
  };

  return (
    <ViewWrapper flex={{ gap: 2 }}>
      <Box
        sx={{
          display: "flex",
          overflow: "auto",
          flex: 1,
        }}
      >
        <LauncherHistory study={study} />
        <Notes study={study} />
      </Box>
      <Divider />
      <Box sx={{ display: "flex", gap: 2 }}>
        <Box sx={{ display: "flex", gap: 2, flex: 1 }}>
          <Button
            variant="contained"
            onClick={() => {
              navigate(`/studies/${study.id}/explore`);
            }}
          >
            {t("global.open")}
          </Button>
          {!study.archived && (
            <Button
              variant="outlined"
              onClick={() => (study.managed ? setOpenVariantModal(true) : importStudy(study))}
            >
              {study.managed ? t("variants.createNewVariant") : t("studies.importcopy")}
            </Button>
          )}
        </Box>
        <Button
          variant="contained"
          onClick={
            study.archived
              ? () => {
                  unarchiveStudy(study);
                }
              : () => setOpenLauncherModal(true)
          }
        >
          {study.archived ? t("global.unarchive") : t("global.launch")}
        </Button>
      </Box>
      {openVariantModal && (
        <CreateVariantDialog
          parentId={study.id}
          open={openVariantModal}
          onClose={() => setOpenVariantModal(false)}
          variantTree={variantTree}
        />
      )}
      {openLauncherModal && (
        <LaunchStudyDialog
          open={openLauncherModal}
          studyIds={[study.id]}
          onClose={() => setOpenLauncherModal(false)}
        />
      )}
    </ViewWrapper>
  );
}

export default InformationView;
