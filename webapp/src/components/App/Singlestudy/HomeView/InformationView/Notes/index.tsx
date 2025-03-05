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
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import type { AxiosError } from "axios";
import { Box, Divider, Skeleton, styled, Typography } from "@mui/material";
import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import LinearScaleIcon from "@mui/icons-material/LinearScale";
import StorageIcon from "@mui/icons-material/Storage";
import HubIcon from "@mui/icons-material/Hub";
import { Editor, EditorState } from "draft-js";
import "draft-js/dist/Draft.css";
import { LoadingButton } from "@mui/lab";
import EditIcon from "@mui/icons-material/Edit";
import { editComments, getComments, getStudyDiskUsage } from "../../../../../../services/api/study";
import { convertSize, convertXMLToDraftJS, getColorForSize } from "./utils";
import type { StudyMetadata } from "../../../../../../types/types";
import NoteEditorModal from "./NodeEditorModal";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import DetailsList from "./DetailsList";
import { getAreas, getLinks } from "../../../../../../redux/selectors";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { PromiseStatus } from "../../../../../../hooks/usePromise";

const Root = styled(Box)(() => ({
  flex: "0 0 40%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  overflow: "hidden",
}));

const Note = styled(Box)(({ theme }) => ({
  flex: 1,
  width: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  padding: theme.spacing(2),
  paddingTop: 0,
}));

const NoteHeader = styled(Box)(() => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  height: "60px",
  boxSizing: "border-box",
}));

const NoteFooter = NoteHeader;

const EditorContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  width: "100%",
  height: 0,
  flex: 1,
  padding: theme.spacing(0),
  overflow: "auto",
}));

interface Props {
  study: StudyMetadata;
}

function Notes({ study }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [editorState, setEditorState] = useState(() => EditorState.createEmpty());
  const [editionMode, setEditionMode] = useState<boolean | "loading">(false);
  const [content, setContent] = useState("");
  const { status: synthesisStatus } = useStudySynthesis({ studyId: study.id });
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const links = useAppSelector((state) => getLinks(state, study.id));

  const { data: diskUsage, isLoading: isDiskUsageLoading } = usePromiseWithSnackbarError(
    () => getStudyDiskUsage(study.id),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [study?.id],
    },
  );

  const commentRes = usePromiseWithSnackbarError(() => getComments(study.id), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [study?.id],
  });

  useEffect(() => {
    const comments = commentRes.data;
    if (comments) {
      setEditorState(EditorState.createWithContent(convertXMLToDraftJS(comments)));
      setContent(comments);
    }
  }, [commentRes.data]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave = async (newContent: string) => {
    const prevEditorState = editorState;
    setEditionMode("loading");
    setEditorState(EditorState.createWithContent(convertXMLToDraftJS(newContent)));

    try {
      await editComments(study.id, newContent);

      setContent(newContent);
      enqueueSnackbar(t("study.success.commentsSaved"), {
        variant: "success",
      });
    } catch (e) {
      setEditorState(prevEditorState);
      enqueueErrorSnackbar(t("study.error.commentsNotSaved"), e as AxiosError);
    }

    setEditionMode(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Note>
        <NoteHeader>
          <StickyNote2OutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <Typography color="text.secondary">{t("study.notes")}</Typography>
        </NoteHeader>

        <UsePromiseCond
          response={commentRes}
          ifFulfilled={() => (
            <>
              <EditorContainer>
                <Editor
                  readOnly
                  editorState={editorState}
                  onChange={setEditorState}
                  textAlignment="left"
                />
              </EditorContainer>
              <NoteFooter>
                <LoadingButton
                  variant="text"
                  color="secondary"
                  onClick={() => setEditionMode(true)}
                  loading={editionMode === "loading"}
                  loadingPosition="end"
                  endIcon={<EditIcon />}
                >
                  {t("global.edit")}
                </LoadingButton>
              </NoteFooter>
            </>
          )}
        />
      </Note>
      <Divider flexItem variant="middle" />
      <Box
        sx={{
          display: "flex",
          alignItems: "flex-start",
          overflowY: "auto",
          width: 1,
        }}
      >
        <DetailsList
          items={[
            {
              content: isDiskUsageLoading ? <Skeleton width={100} /> : convertSize(diskUsage || 0),
              label: t("study.diskUsage"),
              icon: StorageIcon,
              iconColor: getColorForSize(diskUsage || 0),
            },
            {
              content:
                synthesisStatus === PromiseStatus.Fulfilled ? (
                  areas.length
                ) : (
                  <Skeleton width={100} />
                ),
              label: t("study.areas"),
              icon: HubIcon,
            },
            {
              content:
                synthesisStatus === PromiseStatus.Fulfilled ? (
                  links.length
                ) : (
                  <Skeleton width={100} />
                ),
              label: t("study.links"),
              icon: LinearScaleIcon,
            },
          ]}
        />
      </Box>
      {editionMode === true && (
        <NoteEditorModal
          open
          content={content}
          onClose={() => setEditionMode(false)}
          onSave={handleSave}
        />
      )}
    </Root>
  );
}

export default Notes;
