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

import { Fragment } from "react";
import { Box, Typography, Divider, Tooltip } from "@mui/material";
import type { CommandItem } from "../../commandTypes";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import { format, formatDistanceToNow, parseISO } from "date-fns";
import { enUS, fr } from "date-fns/locale";
import { useTranslation } from "react-i18next";
import { getCurrentLanguage } from "@/utils/i18nUtils";

interface Props {
  item: CommandItem;
}

const formatDate = (dateStr: string) => {
  const utcDate = parseISO(dateStr + "Z");
  return format(utcDate, "dd/MM/yyyy HH:mm");
};

const formatDateWithLocale = (dateStr: string) => {
  const date = parseISO(dateStr);
  const lang = getCurrentLanguage();
  const locale = lang.startsWith("fr") ? fr : enUS;

  return formatDistanceToNow(date, {
    addSuffix: true,
    locale,
  });
};

function CommandDetails({ item }: Props) {
  const [t] = useTranslation();
  const details = [
    {
      icon: <PersonOutlineOutlinedIcon sx={{ fontSize: 20 }} />,
      text: item.user || t("global.unknown"),
    },
    {
      icon: <UpdateOutlinedIcon sx={{ fontSize: 20 }} />,
      text: item.updatedAt ? formatDate(item.updatedAt) : t("global.unknown"),
      tooltip: item.updatedAt ? formatDateWithLocale(item.updatedAt) : t("global.unknown"),
    },
  ];

  return (
    <Box sx={{ display: "flex" }}>
      {details.map((detail, index) => (
        <Fragment key={index}>
          {index > 0 && <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />}
          <Box sx={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {detail.icon}
            {detail.tooltip ? (
              <Tooltip title={detail.tooltip}>
                <Typography sx={{ fontSize: "12px" }}>{detail.text}</Typography>
              </Tooltip>
            ) : (
              <Typography sx={{ fontSize: "12px" }}>{detail.text}</Typography>
            )}
          </Box>
        </Fragment>
      ))}
    </Box>
  );
}

export default CommandDetails;
