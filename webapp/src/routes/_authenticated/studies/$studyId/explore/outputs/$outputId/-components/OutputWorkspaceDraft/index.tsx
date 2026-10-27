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

import RouterButton from "@/components/router/RouterButton";
import SelectFE from "@/components/fieldEditors/SelectFE";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import FolderOpenOutlinedIcon from "@mui/icons-material/FolderOpenOutlined";
import {
  Box,
  Button,
  Chip,
  Drawer,
  Stack,
  Tab,
  Tabs,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import OutputFilesPanel from "../OutputFilesPanel";

export type WorkspaceVariant = "drawer" | "tabs" | "explorer" | "fixed";

interface WorkspaceContent {
  variant: WorkspaceVariant;
  filesActive: boolean;
  fileCount: number | undefined;
  onOpenFiles: VoidFunction;
  onShowResults: VoidFunction;
  filesPanel: React.ReactNode;
}

interface Props {
  outputName: string;
  children: (workspace: WorkspaceContent) => React.ReactNode;
}

type FilesState = "ready" | "empty" | "error" | "loading";

function OutputWorkspaceDraft({ outputName, children }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate({
    from: "/studies/$studyId/explore/outputs/$outputId",
  });
  const [variant, setVariant] = useState<WorkspaceVariant>(() => {
    const requestedVariant = new URLSearchParams(window.location.search).get("design");
    return requestedVariant === "drawer" ||
      requestedVariant === "tabs" ||
      requestedVariant === "explorer"
      ? requestedVariant
      : "fixed";
  });
  const [filesActive, setFilesActive] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filesState, setFilesState] = useState<FilesState>("ready");
  const [fileSearch, setFileSearch] = useState("");
  const usesFilesDrawer = variant === "drawer" || variant === "fixed";

  const showResults = () => setFilesActive(false);
  const openFiles = () => {
    if (usesFilesDrawer) {
      setDrawerOpen(true);
    } else {
      setFilesActive(true);
    }
  };
  const isFullFilesView = filesActive && variant !== "explorer";
  const fileCount = filesState === "ready" ? 10 : filesState === "empty" ? 0 : undefined;
  const filesPanel = (
    <OutputFilesPanel
      key={filesState}
      outputName={outputName}
      expanded
      state={filesState}
      search={fileSearch}
      onSearchChange={setFileSearch}
    />
  );

  return (
    <Stack
      direction="column"
      sx={{
        height: 1,
        minHeight: 0,
        overflow: "hidden",
        bgcolor: "background.paper",
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        gap={1.5}
        sx={{
          px: 2,
          py: 0.5,
          minHeight: 37,
          flexWrap: "wrap",
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "action.hover",
        }}
      >
        <Typography variant="caption" color="text.secondary" sx={{ mr: "auto" }}>
          {t("outputDesign.preview")}
        </Typography>
        <ToggleButtonGroup
          exclusive
          size="small"
          value={variant}
          aria-label={t("outputDesign.layout")}
          onChange={(_event, next: WorkspaceVariant | null) => {
            if (next) {
              setVariant(next);
              setFilesActive(false);
              setDrawerOpen(false);
              void navigate({
                search: (previous) => ({ ...previous, design: next, present: undefined }),
                replace: true,
                resetScroll: false,
              });
            }
          }}
          sx={{
            "& .MuiToggleButton-root": { px: 1.25, py: 0.25, fontSize: 11 },
          }}
        >
          <ToggleButton value="drawer">{t("outputDesign.variantA")}</ToggleButton>
          <ToggleButton value="tabs">{t("outputDesign.variantB")}</ToggleButton>
          <ToggleButton value="explorer">{t("outputDesign.variantC")}</ToggleButton>
          <ToggleButton value="fixed">{t("outputDesign.variantD")}</ToggleButton>
        </ToggleButtonGroup>
        <SelectFE<FilesState>
          size="extra-small"
          label={t("outputDesign.fileState")}
          value={filesState}
          onChange={(event) => setFilesState(event.target.value)}
          options={[
            { value: "ready", label: t("outputDesign.ready") },
            { value: "empty", label: t("outputDesign.empty") },
            { value: "error", label: t("outputDesign.error") },
            { value: "loading", label: t("outputDesign.loading") },
          ]}
          sx={{ minWidth: 108 }}
        />
      </Stack>

      <Stack
        data-testid="output-run-header"
        direction="row"
        alignItems="center"
        gap={1.5}
        sx={{
          px: 2,
          height: 44,
          flexShrink: 0,
          borderBottom: 1,
          borderColor: "divider",
          minWidth: 0,
        }}
      >
        <RouterButton
          to=".."
          size="small"
          color="inherit"
          startIcon={<ArrowBackIcon />}
          sx={{ whiteSpace: "nowrap", color: "text.secondary" }}
        >
          {t("outputDesign.backToOutputs")}
        </RouterButton>
        <Box
          sx={{
            borderLeft: 1,
            borderColor: "divider",
            pl: 1.5,
            minWidth: 0,
            flex: 1,
          }}
        >
          <Typography variant="subtitle2" noWrap title={outputName} sx={{ fontWeight: 600 }}>
            {outputName}
          </Typography>
        </Box>
        {usesFilesDrawer && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<FolderOpenOutlinedIcon />}
            onClick={openFiles}
            aria-haspopup="dialog"
            sx={{ flexShrink: 0, px: 1.5, gap: 1, minHeight: 32 }}
          >
            {t("outputDesign.outputFiles")}
            {fileCount !== undefined && (
              <Chip label={fileCount} size="small" sx={{ height: 20, fontSize: 11 }} />
            )}
          </Button>
        )}
      </Stack>

      {variant === "tabs" && (
        <Tabs
          value={filesActive ? "files" : "results"}
          onChange={(_event, value: string) => setFilesActive(value === "files")}
          aria-label={t("outputDesign.outputSections")}
          sx={{ px: 2, borderBottom: 1, borderColor: "divider", minHeight: 42 }}
        >
          <Tab label={t("outputDesign.results")} value="results" sx={{ minHeight: 42 }} />
          <Tab
            value="files"
            icon={<FolderOpenOutlinedIcon sx={{ fontSize: 17 }} />}
            iconPosition="start"
            label={`${t("outputDesign.outputFiles")}${fileCount !== undefined ? ` (${fileCount})` : ""}`}
            sx={{ minHeight: 42 }}
          />
        </Tabs>
      )}

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <Box
          aria-hidden={isFullFilesView || undefined}
          inert={isFullFilesView}
          sx={{
            height: 1,
            visibility: isFullFilesView ? "hidden" : "visible",
            pointerEvents: isFullFilesView ? "none" : undefined,
          }}
        >
          {children({
            variant,
            filesActive,
            fileCount,
            onOpenFiles: openFiles,
            onShowResults: showResults,
            filesPanel,
          })}
        </Box>

        {isFullFilesView && (
          <Stack
            direction="column"
            sx={{
              position: "absolute",
              inset: 0,
              minHeight: 0,
              overflow: "hidden",
              bgcolor: "background.paper",
            }}
          >
            {usesFilesDrawer && (
              <Box sx={{ px: 2, pt: 1 }}>
                <Button size="small" startIcon={<ArrowBackIcon />} onClick={showResults}>
                  {t("outputDesign.backToResults")}
                </Button>
              </Box>
            )}
            {filesPanel}
          </Stack>
        )}
      </Box>

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        slotProps={{
          backdrop: { sx: { bgcolor: "rgba(0, 0, 0, 0.22)" } },
          paper: {
            role: "dialog",
            "aria-modal": true,
            "aria-label": t("outputDesign.outputFiles"),
            sx: { width: 540, maxWidth: "100vw" },
          },
        }}
      >
        <OutputFilesPanel
          key={filesState}
          outputName={outputName}
          state={filesState}
          search={fileSearch}
          onSearchChange={setFileSearch}
          onClose={() => setDrawerOpen(false)}
          onExpand={() => {
            setDrawerOpen(false);
            setFilesActive(true);
          }}
        />
      </Drawer>
    </Stack>
  );
}

export default OutputWorkspaceDraft;
