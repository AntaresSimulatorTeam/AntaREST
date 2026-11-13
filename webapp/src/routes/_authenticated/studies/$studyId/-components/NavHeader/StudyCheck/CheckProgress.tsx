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

import { Box, Button, LinearProgress, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getProgressPercent, type StudyCheckState } from "./utils";

function useElapsedSeconds() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = window.setInterval(
      () => setSeconds(Math.round((Date.now() - start) / 1000)),
      1000,
    );
    return () => window.clearInterval(timer);
  }, []);

  return seconds;
}

interface Props {
  state: StudyCheckState;
  onCancel: VoidFunction;
}

// Progress of a running check: the current step, with a percentage while the rules run
// (the only step whose duration can be predicted), and the elapsed time.
function CheckProgress({ state, onCancel }: Props) {
  const { t } = useTranslation();
  const seconds = useElapsedSeconds();
  const percent = getProgressPercent(state);
  const { progress, phase } = state;

  return (
    <Stack direction="column" spacing={1} role="status">
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "baseline" }}>
        <Typography variant="body2" sx={{ fontWeight: "bold" }}>
          {t(`study.check.phase.${phase}`)}
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          {percent !== undefined && `${percent} % · `}
          {t("study.check.elapsed", { seconds })}
        </Typography>
      </Stack>
      <LinearProgress
        variant={percent === undefined ? "indeterminate" : "determinate"}
        value={percent}
        aria-label={t(`study.check.phase.${phase}`)}
      />
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {progress
            ? t("study.check.step", {
                // The step being run is the one after those already done
                current: Math.min(progress.current + 1, progress.total),
                total: progress.total,
                rule: progress.rule
                  ? t(`study.check.rule.${progress.rule}`, { defaultValue: progress.rule })
                  : "",
              })
            : t(`study.check.phaseHint.${phase}`)}
        </Typography>
        <Box sx={{ flexShrink: 0 }}>
          <Button size="extra-small" color="inherit" onClick={onCancel}>
            {t("global.cancel")}
          </Button>
        </Box>
      </Stack>
    </Stack>
  );
}

export default CheckProgress;
