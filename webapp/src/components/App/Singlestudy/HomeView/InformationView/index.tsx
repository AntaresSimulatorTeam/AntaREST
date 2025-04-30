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

import { useState } from "react";
import { Button, Box, Divider } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { AxiosError } from "axios";
import type { StudyMetadata, VariantTree } from "../../../../../types/types";
import CreateVariantDialog from "./CreateVariantDialog";
import LauncherHistory from "./LauncherHistory";
import Notes from "./Notes";
import LauncherDialog from "../../../Studies/LauncherDialog";
import { copyStudy, unarchiveStudy as callUnarchiveStudy } from "../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import ViewWrapper from "@/components/common/page/ViewWrapper";

interface Props {
  study: StudyMetadata | undefined;
  tree: VariantTree | undefined;
}

function InformationView(props: Props) {
  const { study, tree } = props;
  const navigate = useNavigate();
  const [t] = useTranslation();
  const [openVariantModal, setOpenVariantModal] = useState<boolean>(false);
  const [openLauncherModal, setOpenLauncherModal] = useState<boolean>(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const importStudy = async (study: StudyMetadata) => {
    try {
      await copyStudy(study.id, `${study.name} (${t("studies.copySuffix")})`, false);
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
        {study && <Notes study={study} />}
      </Box>
      <Divider />
      <Box sx={{ display: "flex", gap: 2 }}>
        <Box sx={{ display: "flex", gap: 2, flex: 1 }}>
          <Button
            variant="contained"
            onClick={() => {
              if (study) {
                navigate(`/studies/${study.id}/explore`);
              }
            }}
          >
            {t("global.open")}
          </Button>
          {study && !study.archived && (
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
            study?.archived
              ? () => {
                  unarchiveStudy(study);
                }
              : () => setOpenLauncherModal(true)
          }
        >
          {study?.archived ? t("global.unarchive") : t("global.launch")}
        </Button>
      </Box>
      {study && tree && openVariantModal && (
        <CreateVariantDialog
          parentId={study.id}
          open={openVariantModal}
          onClose={() => setOpenVariantModal(false)}
          tree={tree}
        />
      )}
      {study && openLauncherModal && (
        <LauncherDialog
          open={openLauncherModal}
          studyIds={[study.id]}
          onClose={() => setOpenLauncherModal(false)}
        />
      )}
    </ViewWrapper>
  );
}

export default InformationView;
