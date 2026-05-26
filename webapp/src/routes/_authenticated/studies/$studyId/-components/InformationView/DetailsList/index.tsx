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

import { PromiseStatus } from "@/hooks/usePromise";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import useAppSelector from "@/redux/hooks/useAppSelector";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getAreas, getLinks } from "@/redux/selectors";
import { getStudyDiskUsage } from "@/services/api/study";
import HubIcon from "@mui/icons-material/Hub";
import LinearScaleIcon from "@mui/icons-material/LinearScale";
import StorageIcon from "@mui/icons-material/Storage";
import { Avatar, List, ListItem, ListItemAvatar, ListItemText, Skeleton } from "@mui/material";
import { useTranslation } from "react-i18next";
import useStudy from "../../../-hooks/useStudy";
import { convertSize, getColorForSize } from "./utils";

interface DetailsListItem {
  content: React.ReactNode;
  label: string;
  icon: React.ReactNode;
  iconColor?: string;
}

function DetailsList() {
  const { t } = useTranslation();
  const study = useStudy();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const links = useAppSelector((state) => getLinks(state, study.id));
  const { status: synthesisStatus } = useStudySynthesis({ studyId: study.id });

  const { data: diskUsage, isLoading: isDiskUsageLoading } = usePromiseWithSnackbarError(
    () => getStudyDiskUsage(study.id),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study.id],
      disabled: !study.managed,
    },
  );

  const items = [
    study.managed && {
      content: isDiskUsageLoading ? <Skeleton width={100} /> : convertSize(diskUsage || 0),
      label: t("study.diskUsage"),
      icon: <StorageIcon />,
      iconColor: getColorForSize(diskUsage || 0),
    },
    {
      content:
        synthesisStatus === PromiseStatus.Fulfilled ? areas.length : <Skeleton width={100} />,
      label: t("study.areas"),
      icon: <HubIcon />,
    },
    {
      content:
        synthesisStatus === PromiseStatus.Fulfilled ? links.length : <Skeleton width={100} />,
      label: t("study.links"),
      icon: <LinearScaleIcon />,
    },
  ].filter(Boolean) satisfies DetailsListItem[];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <List dense disablePadding sx={{ p: 1, pb: 0, overflow: "auto" }}>
      {items.map((item) => (
        <ListItem key={item.label} disablePadding>
          <ListItemAvatar>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                backgroundColor: item.iconColor || "default",
              }}
            >
              {item.icon}
            </Avatar>
          </ListItemAvatar>
          <ListItemText primary={item.content} secondary={item.label} />
        </ListItem>
      ))}
    </List>
  );
}

export default DetailsList;
