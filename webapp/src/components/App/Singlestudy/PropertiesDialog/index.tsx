import { useEffect, useMemo, useState } from "react";
import { isEqual } from "lodash";
import debug from "debug";
import { Button, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import SingleSelect from "../../../common/SelectSingle";
import MultiSelect from "../../../common/SelectMulti";
import {
  StudyMetadata,
  StudyMetadataPatchDTO,
  StudyPublicMode,
} from "../../../../common/types";
import TextSeparator from "../../../common/TextSeparator";
import {
  addStudyGroup,
  changePublicMode,
  deleteStudyGroup,
  updateStudyMetadata,
} from "../../../../services/api/study";
import { getGroups } from "../../../../services/api/user";
import TagTextInput from "../../../common/TagTextInput";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../../common/dialogs/BasicDialog";
import { ElementContainer, InputElement, Root } from "./style";
import { PUBLIC_MODE_LIST } from "../../../common/utils/constants";
import usePromiseWithSnackbarError from "../../../../hooks/usePromiseWithSnackbarError";

const logErr = debug("antares:createstudyform:error");

interface Props {
  open: boolean;
  onClose: () => void;
  study: StudyMetadata;
}

function PropertiesModal(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, study } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  // NOTE: GET TAG LIST FROM BACKEND
  const tagList: Array<string> = [];

  const [studyName, setStudyName] = useState<string>(study.name);
  const [publicMode, setPublicMode] = useState<StudyPublicMode>(
    study.publicMode
  );
  const [group, setGroup] = useState<Array<string>>(
    study.groups.map((elm) => elm.id)
  );
  const [tags, setTags] = useState<Array<string>>(study.tags ? study.tags : []);
  const [dataChanged, setDataChanged] = useState<boolean>(false);

  const initStudyName = useMemo(() => study.name, [study]);
  const initPublicMode = useMemo(() => study.publicMode, [study]);
  const initGroup = useMemo(() => study.groups.map((elm) => elm.id), [study]);
  const initTags = useMemo(() => study.tags, [study]);

  const tagChanged = useMemo((): boolean => {
    let tpmTagsChanged = false;
    if (initTags) {
      tpmTagsChanged = tags ? !isEqual(initTags, tags) : true;
    } else {
      tpmTagsChanged = tags.length > 0;
    }
    return tpmTagsChanged;
  }, [initTags, tags]);

  const { data: groupList = [] } = usePromiseWithSnackbarError(getGroups, {
    errorMessage: t("settings.error.groupsError"),
  });

  useEffect(() => {
    if (study) {
      setStudyName(study.name);
      setPublicMode(study.publicMode);
      setGroup(study.groups.map((elm) => elm.id));
      setTags(study.tags ? study.tags : []);
    }
  }, [study]);

  useEffect(() => {
    setDataChanged(
      initStudyName !== studyName ||
        initPublicMode !== publicMode ||
        !isEqual(initGroup, group) ||
        tagChanged
    );
  }, [
    studyName,
    publicMode,
    group,
    tags,
    initStudyName,
    initPublicMode,
    initGroup,
    tagChanged,
  ]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async () => {
    if (studyName && studyName.replace(/\s+/g, "") !== "") {
      try {
        const sid = study.id;

        const newMetadata: StudyMetadataPatchDTO = {
          name: initStudyName !== studyName ? studyName : initStudyName,
          tags: tagChanged ? tags : study.tags,
        };
        // Update metadata
        if (tagChanged || initStudyName !== studyName) {
          await updateStudyMetadata(sid, newMetadata);
        }

        // Update public mode
        if (initPublicMode !== publicMode) {
          await changePublicMode(sid, publicMode);
        }

        // Update group
        if (!isEqual(initGroup, group)) {
          await Promise.all(
            initGroup.map(async (elm) => {
              if (group.findIndex((item) => item === elm) < 0) {
                await deleteStudyGroup(sid, elm);
              }
            })
          );

          await Promise.all(
            group.map(async (elm) => {
              if (initGroup.findIndex((item) => item === elm) < 0) {
                await addStudyGroup(sid, elm);
              }
            })
          );
        }
        enqueueSnackbar(
          t("study.success.modifiedStudy", { studyname: studyName }),
          { variant: "success" }
        );
      } catch (e) {
        logErr("Failed to modify study", studyName, e);
        enqueueErrorSnackbar(
          t("study.error.modifiedStudy", { studyname: studyName }),
          e as AxiosError
        );
      }
      onClose();
    } else {
      enqueueSnackbar(t("global.error.emptyName"), { variant: "error" });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("study.properties")}
      contentProps={{
        sx: { width: "600px", height: "350px", p: 0 },
      }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={handleSubmit}
            disabled={!dataChanged}
          >
            {t("study.validate")}
          </Button>
        </>
      }
    >
      <Root>
        <InputElement>
          <TextField
            variant="filled"
            label={t("studies.studyName")}
            value={studyName}
            onChange={(ev) => setStudyName(ev.target.value)}
            sx={{ flexGrow: 1 }}
            required
          />
        </InputElement>
        <ElementContainer>
          <TextSeparator text={t("global.permission")} />
          <InputElement>
            <SingleSelect
              name={t("study.publicMode")}
              list={PUBLIC_MODE_LIST}
              data={publicMode}
              setValue={(value: string) =>
                setPublicMode(value as StudyPublicMode)
              }
              sx={{ flexGrow: 1, mr: 1, height: "60px" }}
            />
            <MultiSelect
              name={t("global.group")}
              list={groupList}
              data={group}
              setValue={setGroup}
              sx={{ flexGrow: 1, ml: 1, height: "60px" }}
            />
          </InputElement>
        </ElementContainer>
        <ElementContainer>
          <TextSeparator text="Metadata" />
          <InputElement>
            <TagTextInput
              label={t("studies.enterTag")}
              sx={{ flexGrow: 1 }}
              value={tags}
              onChange={setTags}
              tagList={tagList}
              required
            />
          </InputElement>
        </ElementContainer>
      </Root>
    </BasicDialog>
  );
}

export default PropertiesModal;
