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

import { useEffect, useState } from "react";
import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { AxiosError } from "axios";
import { isStringEmpty, isUserAdmin } from "../../../services/utils";
import * as api from "../../../services/api/maintenance";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import OkDialog from "../../common/dialogs/OkDialog";
import { setMessageInfo } from "../../../redux/ducks/ui";
import { getAuthUser, getMessageInfo } from "../../../redux/selectors";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import InfoIcon from "@mui/icons-material/Info";
import { useMount } from "react-use";

function MessageInfoDialog() {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [open, setOpen] = useState(false);
  const user = useAppSelector(getAuthUser);
  const messageInfo = useAppSelector(getMessageInfo);
  const dispatch = useAppDispatch();

  useMount(async () => {
    try {
      const tmpMessage = await api.getMessageInfo();
      dispatch(setMessageInfo(isStringEmpty(tmpMessage) ? "" : tmpMessage));
    } catch (e) {
      enqueueErrorSnackbar(t("maintenance.error.messageInfoError"), e as AxiosError);
    }
  });

  useEffect(() => {
    if (messageInfo && (user === undefined || !isUserAdmin(user))) {
      setOpen(true);
    }
  }, [messageInfo, user]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <OkDialog
      open={open}
      title="Information"
      titleIcon={InfoIcon}
      alert="info"
      maxWidth="xs"
      fullWidth
      onOk={() => setOpen(false)}
    >
      <Typography style={{ whiteSpace: "pre-wrap" }}>{messageInfo}</Typography>
    </OkDialog>
  );
}

export default MessageInfoDialog;
