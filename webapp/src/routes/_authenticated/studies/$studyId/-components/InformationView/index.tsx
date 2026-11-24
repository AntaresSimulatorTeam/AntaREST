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

import CustomScrollbar from "@/components/CustomScrollbar";
import ViewWrapper from "@/components/page/ViewWrapper";
import RouterButton from "@/components/router/RouterButton";
import RouterLink from "@/components/router/RouterLink";
import useDialog from "@/hooks/useDialog";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getReferenceStudy } from "@/redux/selectors";
import { copyStudy } from "@/services/api/studies";
import { unarchiveStudy } from "@/services/api/study";
import { toError } from "@/utils/fnUtils";
import BoltIcon from "@mui/icons-material/Bolt";
import UnarchiveOutlinedIcon from "@mui/icons-material/UnarchiveOutlined";
import { Alert, Box, Button, Divider, Stack } from "@mui/material";
import { Trans, useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";
import useStudyVariantTree from "../../-hooks/useStudyVariantTree";
import LaunchStudiesDialog from "../../../../../-shared/components/studies/dialogs/LaunchStudiesDialog";
import CreateStudyVariantDialog from "./CreateStudyVariantDialog";
import DetailsList from "./DetailsList";
import LauncherHistory from "./LauncherHistory";
import Notes from "./Notes";

function InformationView() {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { openDialog } = useDialog();
  const study = useStudy();
  const { data: variantTree } = useStudyVariantTree({ studyId: study.id });
  const referenceStudy = useAppSelector((state) => getReferenceStudy(state, study.id));

  // When the reference study is archived, all its variants are considered archived as well
  const isArchived = referenceStudy.archived;
  const isVariant = study.type === "variantstudy";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCopyStudy = async () => {
    try {
      await copyStudy({
        studyId: study.id,
        studyName: `${study.name} (${t("studies.copySuffix")})`,
        withOutputs: false,
      });
    } catch (err) {
      enqueueErrorSnackbar(t("studies.error.copyStudy"), toError(err));
    }
  };

  const handleUnarchiveReferenceStudy = async () => {
    try {
      // Only the reference study can be archived/unarchived
      await unarchiveStudy(referenceStudy.id);
    } catch (err) {
      enqueueErrorSnackbar(
        t("studies.error.unarchive", { studyname: referenceStudy.name }),
        toError(err),
      );
    }
  };

  const handleCreateVariant = () => {
    openDialog(({ onClose }) => (
      <CreateStudyVariantDialog
        defaultParentId={study.id}
        variantTree={variantTree}
        onClose={onClose}
      />
    ));
  };

  const handleLaunchStudy = () => {
    openDialog(({ onClose }) => (
      <LaunchStudiesDialog open studyIds={[study.id]} onClose={onClose} />
    ));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper flex={{ gap: 2 }}>
      {isArchived && isVariant && (
        <Alert severity="warning">
          <Trans
            i18nKey="variants.unarchive.warning"
            values={{ referenceStudyName: referenceStudy.name }}
            components={{
              referenceStudyLink: (
                <RouterLink to="/studies/$studyId" params={{ studyId: referenceStudy.id }} />
              ),
            }}
          />
        </Alert>
      )}

      <Stack flex={1} spacing={1} sx={{ overflow: "auto" }}>
        <LauncherHistory />
        {!isArchived && (
          <Stack direction="column" sx={{ height: 1, flex: 1, overflow: "hidden" }}>
            <Notes />
            <Divider flexItem variant="middle" />
            <DetailsList />
          </Stack>
        )}
      </Stack>

      <Divider flexItem />

      <Box>
        <CustomScrollbar>
          <Stack spacing={1} justifyContent="space-between">
            <Stack spacing={1}>
              {!isArchived && (
                <>
                  <RouterButton
                    variant="contained"
                    to="/studies/$studyId/explore"
                    params={{ studyId: study.id }}
                  >
                    {t("button.explore")}
                  </RouterButton>
                  {study.managed ? (
                    <Button variant="outlined" onClick={handleCreateVariant}>
                      {t("variants.createNewVariant")}
                    </Button>
                  ) : (
                    <Button variant="outlined" onClick={handleCopyStudy}>
                      {t("studies.importcopy")}
                    </Button>
                  )}
                </>
              )}
            </Stack>
            {isArchived ? (
              <Button
                variant="contained"
                onClick={handleUnarchiveReferenceStudy}
                startIcon={<UnarchiveOutlinedIcon />}
              >
                {isVariant ? t("variants.unarchive") : t("global.unarchive")}
              </Button>
            ) : (
              <Button variant="contained" onClick={handleLaunchStudy} startIcon={<BoltIcon />}>
                {t("global.launch")}
              </Button>
            )}
          </Stack>
        </CustomScrollbar>
      </Box>
    </ViewWrapper>
  );
}

export default InformationView;
