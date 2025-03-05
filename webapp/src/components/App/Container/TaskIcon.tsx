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

import useAppSelector from "@/redux/hooks/useAppSelector";
import { getTaskNotificationsCount } from "@/redux/selectors";
import { Badge } from "@mui/material";
import AssignmentIcon from "@mui/icons-material/Assignment";

function TaskIcon() {
  const notificationCount = useAppSelector(getTaskNotificationsCount);

  return (
    <Badge
      badgeContent={notificationCount}
      color="primary"
      sx={{
        ".MuiBadge-badge": {
          right: -4,
          top: 11,
          border: `2px solid`,
          borderColor: "background.paper",
          padding: "0 4px",
        },
      }}
    >
      <AssignmentIcon color="action" />
    </Badge>
  );
}

export default TaskIcon;
