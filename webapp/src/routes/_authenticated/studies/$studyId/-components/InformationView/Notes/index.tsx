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

import UsePromiseCond from "@/components/utils/UsePromiseCond";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { editComments, getComments } from "@/services/api/study";
import EditIcon from "@mui/icons-material/Edit";
import StickyNote2OutlinedIcon from "@mui/icons-material/StickyNote2Outlined";
import { Box, Button, styled, Typography } from "@mui/material";
import type { AxiosError } from "axios";
import { Editor, EditorState } from "draft-js";
import "draft-js/dist/Draft.css";
import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../../-hooks/useStudy";
import NoteEditorModal from "./NodeEditorModal";
import { convertXMLToDraftJS } from "./utils";

const Note = styled(Box)(({ theme }) => ({
  flex: 1,
  width: "100%",
  display: "flex",
  flexDirection: "column",
  padding: theme.spacing(1),
}));

const EditorContainer = styled(Box)({
  height: 0,
  flex: 1,
  overflow: "auto",
});

function Notes() {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [editorState, setEditorState] = useState(() => EditorState.createEmpty());
  const [editionMode, setEditionMode] = useState<boolean | "loading">(false);
  const [content, setContent] = useState("");
  const study = useStudy();

  const commentRes = usePromiseWithSnackbarError(() => getComments(study.id), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [study.id],
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
    <>
      <Note>
        <Typography
          color="text.secondary"
          sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}
        >
          <StickyNote2OutlinedIcon />
          {t("study.notes")}
        </Typography>

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
              <Box sx={{ pt: 1 }}>
                <Button
                  variant="text"
                  color="secondary"
                  onClick={() => setEditionMode(true)}
                  loading={editionMode === "loading"}
                  loadingPosition="end"
                  endIcon={<EditIcon />}
                >
                  {t("global.edit")}
                </Button>
              </Box>
            </>
          )}
        />
      </Note>
      {editionMode === true && (
        <NoteEditorModal
          open
          content={content}
          onClose={() => setEditionMode(false)}
          onSave={handleSave}
        />
      )}
    </>
  );
}

export default Notes;
