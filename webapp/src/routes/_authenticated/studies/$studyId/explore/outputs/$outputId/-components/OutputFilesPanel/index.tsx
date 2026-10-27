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

import CloseIcon from "@mui/icons-material/Close";
import CloseFullscreenIcon from "@mui/icons-material/CloseFullscreen";
import CodeIcon from "@mui/icons-material/Code";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import SearchIcon from "@mui/icons-material/Search";
import SearchOffIcon from "@mui/icons-material/SearchOff";
import TableChartOutlinedIcon from "@mui/icons-material/TableChartOutlined";
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  Skeleton,
  Snackbar,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { demoCsv, sampleFiles } from "./sampleFiles";

interface Props {
  outputName: string;
  search: string;
  onSearchChange: (search: string) => void;
  onClose?: () => void;
  onExpand?: () => void;
  expanded?: boolean;
  state?: "ready" | "empty" | "error" | "loading";
}

function OutputFilesPanel({
  outputName,
  search,
  onSearchChange,
  onClose,
  onExpand,
  expanded,
  state = "ready",
}: Props) {
  const { t } = useTranslation();
  const [notice, setNotice] = useState(false);
  const [retried, setRetried] = useState(false);
  const files = sampleFiles.filter(({ path }) =>
    path.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()),
  );
  const ready = state === "ready" || (state === "error" && retried);

  const handleDownload = ({ demo, name }: (typeof sampleFiles)[number]) => {
    if (!demo) {
      setNotice(true);
      return;
    }

    const url = URL.createObjectURL(new Blob([demoCsv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <Stack
      direction="column"
      component="section"
      aria-label={t("outputDesignFiles.title")}
      sx={{
        height: "100%",
        width: 1,
        maxWidth: expanded ? 1080 : undefined,
        mx: expanded ? "auto" : 0,
        minHeight: 0,
        minWidth: 0,
        bgcolor: "background.paper",
      }}
    >
      <Box sx={{ px: 3, pt: 2.5, pb: 2 }}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
          <FolderOpenOutlinedIcon sx={{ color: "primary.main", fontSize: 23 }} />
          <Typography component="h2" variant="h6" sx={{ flex: 1, fontWeight: 650 }}>
            {t("outputDesignFiles.title")}
          </Typography>
          {onExpand && (
            <Tooltip
              title={t(expanded ? "outputDesignFiles.collapse" : "outputDesignFiles.expand")}
            >
              <IconButton
                size="small"
                onClick={onExpand}
                aria-label={t(expanded ? "outputDesignFiles.collapse" : "outputDesignFiles.expand")}
              >
                {expanded ? (
                  <CloseFullscreenIcon fontSize="small" />
                ) : (
                  <OpenInFullIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          )}
          {onClose && (
            <Tooltip title={t("outputDesignFiles.close")}>
              <IconButton size="small" onClick={onClose} aria-label={t("outputDesignFiles.close")}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Stack>
        <Typography variant="body2" color="text.secondary">
          {t("outputDesignFiles.subtitle")}
        </Typography>
        <Typography
          variant="caption"
          title={outputName}
          sx={{
            mt: 0.75,
            display: "block",
            overflowWrap: "anywhere",
            color: "text.secondary",
          }}
        >
          {outputName}
        </Typography>
        {ready && (
          <TextField
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder={t("outputDesignFiles.search")}
            size="small"
            fullWidth
            sx={{ mt: 2 }}
            slotProps={{
              htmlInput: { "aria-label": t("outputDesignFiles.search") },
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: search ? (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      aria-label={t("outputDesignFiles.clear")}
                      onClick={() => onSearchChange("")}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </InputAdornment>
                ) : undefined,
              },
            }}
          />
        )}
      </Box>
      <Divider />

      <Box sx={{ flex: 1, minHeight: 0, overflow: "auto" }}>
        {ready && (
          <>
            <Typography
              component="p"
              variant="caption"
              color="text.secondary"
              aria-live="polite"
              sx={{ px: 3, pt: 1.5, pb: 0.5 }}
            >
              {search
                ? t("outputDesignFiles.matches", {
                    count: files.length,
                    total: sampleFiles.length,
                  })
                : t("outputDesignFiles.count", { count: files.length })}
            </Typography>
            <List disablePadding>
              {files.map((file) => (
                <ListItem
                  key={file.path}
                  disableGutters
                  sx={(theme) => ({
                    px: 3,
                    py: 1.5,
                    gap: 1.5,
                    alignItems: "center",
                    borderBottom: `1px solid ${theme.vars.palette.divider}`,
                    "&:hover": { bgcolor: theme.vars.palette.action.hover },
                  })}
                >
                  <Box
                    sx={{
                      width: 34,
                      height: 38,
                      borderRadius: 1,
                      display: "grid",
                      placeItems: "center",
                      color:
                        file.extension === "CSV" || file.extension === "PARQUET"
                          ? "primary.main"
                          : "text.secondary",
                      bgcolor: "action.hover",
                      flexShrink: 0,
                    }}
                  >
                    {file.extension === "CSV" || file.extension === "PARQUET" ? (
                      <TableChartOutlinedIcon fontSize="small" />
                    ) : file.extension === "JSON" ? (
                      <CodeIcon fontSize="small" />
                    ) : (
                      <DescriptionOutlinedIcon fontSize="small" />
                    )}
                  </Box>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body2" title={file.name} noWrap sx={{ fontWeight: 550 }}>
                      {file.name}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      title={file.folder}
                      noWrap
                      component="p"
                    >
                      {file.folder}/
                    </Typography>
                    {file.demo && (
                      <Typography variant="caption" sx={{ color: "primary.main" }}>
                        {t("outputDesignFiles.demoFile")}
                      </Typography>
                    )}
                  </Box>
                  <Chip
                    label={file.extension}
                    size="small"
                    variant="outlined"
                    sx={{
                      height: 21,
                      fontSize: 10,
                      letterSpacing: 0.3,
                      flexShrink: 0,
                    }}
                  />
                  <Tooltip
                    title={t("outputDesignFiles.download", {
                      path: file.path,
                      interpolation: { escapeValue: false },
                    })}
                  >
                    <IconButton
                      size="small"
                      aria-label={t("outputDesignFiles.download", {
                        path: file.path,
                        interpolation: { escapeValue: false },
                      })}
                      onClick={() => handleDownload(file)}
                      sx={{ flexShrink: 0 }}
                    >
                      <DownloadOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </ListItem>
              ))}
            </List>
            {files.length === 0 && (
              <Stack
                direction="column"
                alignItems="center"
                spacing={1.25}
                sx={{ px: 3, py: 6, textAlign: "center" }}
              >
                <SearchOffIcon sx={{ color: "text.secondary", fontSize: 36 }} />
                <Typography variant="subtitle2">{t("outputDesignFiles.noMatches")}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {t("outputDesignFiles.searchHint")}
                </Typography>
                <Button onClick={() => onSearchChange("")}>{t("outputDesignFiles.clear")}</Button>
              </Stack>
            )}
          </>
        )}
        {state === "empty" && (
          <Stack
            direction="column"
            alignItems="center"
            spacing={1.5}
            sx={{ px: 3, py: 7, textAlign: "center" }}
          >
            <FolderOpenOutlinedIcon sx={{ color: "text.secondary", fontSize: 40 }} />
            <Typography variant="subtitle1">{t("outputDesignFiles.emptyTitle")}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t("outputDesignFiles.emptyBody")}
            </Typography>
          </Stack>
        )}
        {state === "error" && !retried && (
          <Alert
            severity="error"
            sx={{ m: 3 }}
            action={
              <Button color="inherit" onClick={() => setRetried(true)}>
                {t("outputDesignFiles.retry")}
              </Button>
            }
          >
            {t("outputDesignFiles.error")}
          </Alert>
        )}
        {state === "loading" && (
          <Stack
            direction="column"
            spacing={2.5}
            aria-label={t("outputDesignFiles.loading")}
            aria-busy="true"
            sx={{ p: 3 }}
          >
            {Array.from({ length: 6 }, (_, index) => (
              <Stack key={index} direction="row" spacing={1.5} alignItems="center">
                <Skeleton variant="rounded" width={34} height={38} />
                <Box sx={{ flex: 1 }}>
                  <Skeleton width="80%" />
                  <Skeleton width="55%" />
                </Box>
              </Stack>
            ))}
          </Stack>
        )}
      </Box>

      <Divider />
      <Typography variant="caption" color="text.secondary" sx={{ px: 3, py: 1.5 }}>
        {t("outputDesignFiles.sampleNote")}
      </Typography>
      <Snackbar
        open={notice}
        onClose={() => setNotice(false)}
        autoHideDuration={4500}
        message={t("outputDesignFiles.previewDownload")}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      />
    </Stack>
  );
}

export default OutputFilesPanel;
