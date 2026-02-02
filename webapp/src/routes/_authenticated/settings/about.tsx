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

import CopyButton from "@/components/buttons/CopyButton";
import ViewWrapper from "@/components/page/ViewWrapper";
import { GITHUB_URL } from "@/routes/-shared/constants";
import { getConfig } from "@/services/config";
import LaunchIcon from "@mui/icons-material/Launch";
import { IconButton, List, ListItem, ListItemButton, ListItemText } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_authenticated/settings/about")({
  component: About,
});

function About() {
  const { version, gitcommit } = getConfig().versionInfo;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCopyCommitClick = () => {
    navigator.clipboard.writeText(gitcommit);
  };

  const handleProjectHomepageClick = () => {
    window.open(GITHUB_URL, "_blank", "noopener,noreferrer");
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <List dense disablePadding>
        <ListItem
          disablePadding
          secondaryAction={
            <IconButton edge="end" onClick={handleProjectHomepageClick}>
              <LaunchIcon />
            </IconButton>
          }
        >
          <ListItemButton>
            <ListItemText primary="Antares Web" secondary={version} />
          </ListItemButton>
        </ListItem>
        <ListItem
          disablePadding
          secondaryAction={<CopyButton edge="end" onClick={handleCopyCommitClick} />}
        >
          <ListItemButton>
            <ListItemText primary="Commit SHA" secondary={gitcommit} />
          </ListItemButton>
        </ListItem>
      </List>
    </ViewWrapper>
  );
}
