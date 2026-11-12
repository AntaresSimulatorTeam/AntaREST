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

import EmptyView from "@/components/page/EmptyView";
import TabsView from "@/components/page/TabsView";
import RouterButton from "@/components/router/RouterButton";
import RouterLink from "@/components/router/RouterLink";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getReferenceStudy } from "@/redux/selectors";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import { Alert, Stack } from "@mui/material";
import { createFileRoute, linkOptions } from "@tanstack/react-router";
import { Trans, useTranslation } from "react-i18next";
import useStudy from "../-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore")({
  component: StudyExploreLayout,
});

function StudyExploreLayout() {
  const { t } = useTranslation();
  const params = Route.useParams();
  const study = useStudy();
  const referenceStudy = useAppSelector((state) => getReferenceStudy(state, study.id));

  // When the reference study is archived, all its variants are considered archived as well
  const isArchived = referenceStudy.archived;
  const isVariant = study.type === "variantstudy";

  if (isArchived) {
    return (
      <Stack direction="column" sx={{ height: 1 }}>
        {isVariant && (
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
        <EmptyView
          icon={ArchiveOutlinedIcon}
          title={t("study.archived")}
          primaryActions={
            <RouterButton variant="contained" to="/studies/$studyId" params={{ studyId: study.id }}>
              {t("button.back")}
            </RouterButton>
          }
        />
      </Stack>
    );
  }

  return (
    <TabsView
      tabs={[
        {
          id: "modeling",
          label: t("study.modeling"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/modeling",
            params,
          }),
        },
        {
          id: "configuration",
          label: t("study.configuration"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/configuration",
            params,
          }),
        },
        {
          id: "table-modes",
          label: t("study.tableModes"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/table-modes",
            params,
          }),
        },
        {
          id: "xpansion",
          label: "Xpansion",
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/xpansion",
            params,
            search: { reload: undefined },
          }),
        },
        {
          id: "outputs",
          label: t("study.outputs"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/outputs",
            params,
          }),
        },
        study.storageMode === "filesystem" && {
          id: "debug",
          label: t("study.debug"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/debug",
            params,
            search: { path: undefined },
          }),
        },
        study.storageMode === "database" && {
          id: "user-resources",
          label: t("study.userResources"),
          linkOptions: linkOptions({
            to: "/studies/$studyId/explore/user-resources",
            params,
            search: { path: undefined },
          }),
        },
      ].filter(Boolean)}
      divider
    />
  );
}
