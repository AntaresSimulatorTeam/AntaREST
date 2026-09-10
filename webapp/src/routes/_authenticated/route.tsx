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

import rgpd from "@/assets/md/rgpd.md?raw";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import { logout } from "@/redux/ducks/auth";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import storage, { StorageKey } from "@/services/utils/localStorage";
import PolicyIcon from "@mui/icons-material/Policy";
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import Container from "./-components/Container";
import MaintenanceMode from "./-components/MaintenanceMode";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/login",
        search: {
          // Save current location for redirect after login
          redirect: location.href,
        },
      });
    }
  },
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const [openGdprDialog, setOpenGdprDialog] = useState(
    () => !storage.getItem(StorageKey.GdprAccepted),
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAcceptGdpr = () => {
    storage.setItem(StorageKey.GdprAccepted, true);
    setOpenGdprDialog(false);
  };

  const handleRejectGdpr = () => {
    dispatch(logout());
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <MaintenanceMode>
        <Container>
          <Outlet />
        </Container>
      </MaintenanceMode>
      <ConfirmationDialog
        open={openGdprDialog}
        title={t("gdpr.title")}
        titleIcon={PolicyIcon}
        confirmButtonText={t("global.accept")}
        cancelButtonText={t("global.signOut")}
        onConfirm={handleAcceptGdpr}
        onCancel={handleRejectGdpr}
        onlyCloseOnCancel
        fullScreen
      >
        <Markdown>{rgpd}</Markdown>
      </ConfirmationDialog>
    </>
  );
}
