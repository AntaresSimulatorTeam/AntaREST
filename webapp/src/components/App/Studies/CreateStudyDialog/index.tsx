import { useState } from "react";
import debug from "debug";
import { useSnackbar } from "notistack";
import { Button, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { usePromise } from "react-use";
import * as R from "ramda";
import SingleSelect from "../../../common/SelectSingle";
import MultiSelect from "../../../common/SelectMulti";
import { GenericInfo, StudyPublicMode } from "../../../../common/types";
import TextSeparator from "../../../common/TextSeparator";
// import { getGroups } from "../../../../services/api/user";
import TagTextInput from "../../../common/TagTextInput";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog, {
  BasicDialogProps,
} from "../../../common/dialogs/BasicDialog";
import { Root, ElementContainer, InputElement } from "./style";
import { createStudy } from "../../../../redux/ducks/studies";
import {
  getStudyVersionsFormatted,
  getGroups,
} from "../../../../redux/selectors";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";

const logErr = debug("antares:createstudyform:error");

interface Props {
  open: BasicDialogProps["open"];
  onClose: VoidFunction;
}

function CreateStudyModal(props: Props) {
  const [t] = useTranslation();
  const { open, onClose } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const versionList = useAppSelector(getStudyVersionsFormatted);
  const mounted = usePromise();
  const dispatch = useAppDispatch();

  // NOTE: GET TAG LIST FROM BACKEND
  const tagList: Array<string> = [];

  const [version, setVersion] = useState(R.last(versionList)?.id.toString());
  const [studyName, setStudyName] = useState<string>("");
  const [publicMode, setPublicMode] = useState<StudyPublicMode>("NONE");
  const [groups, setGroups] = useState<Array<string>>([]);
  const [tags, setTags] = useState<Array<string>>([]);
  const groupList = useAppSelector(getGroups);
  const [actionButtonDisabled, setActionButtonDisabled] =
    useState<boolean>(false);

  const onSubmit = async () => {
    setActionButtonDisabled(true);
    if (studyName && studyName.replace(/\s+/g, "") !== "") {
      try {
        await mounted(
          dispatch(
            createStudy({
              name: studyName,
              version,
              groups,
              publicMode,
              tags,
            })
          ).unwrap()
        );

        enqueueSnackbar(
          t("studies.success.createStudy", { studyname: studyName }),
          { variant: "success" }
        );
      } catch (e) {
        logErr("Failed to create new study", studyName, e);
        enqueueErrorSnackbar(
          t("studies.error.createStudy", { studyname: studyName }),
          e as AxiosError
        );
      }
      onClose();
    } else {
      enqueueSnackbar(t("global.error.emptyName"), { variant: "error" });
      setActionButtonDisabled(false);
    }
  };

  const publicModeList: Array<GenericInfo> = [
    { id: "NONE", name: t("study.nonePublicMode") },
    { id: "READ", name: t("study.readPublicMode") },
    { id: "EXECUTE", name: t("study.executePublicMode") },
    { id: "EDIT", name: t("global.edit") },
    { id: "FULL", name: t("study.fullPublicMode") },
  ];

  return (
    <BasicDialog
      title={t("studies.createNewStudy")}
      open={open}
      onClose={onClose}
      contentProps={{
        sx: { width: "500px", height: "380px", p: 0, overflow: "hidden" },
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
            onClick={onSubmit}
            disabled={actionButtonDisabled}
          >
            {t("global.create")}
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
            sx={{ flexGrow: 1, mr: 2 }}
            required
          />
          <SingleSelect
            name={t("global.version")}
            list={versionList}
            data={version}
            setValue={setVersion}
            sx={{ flexGrow: 1 }}
            required
          />
        </InputElement>
        <ElementContainer>
          <TextSeparator text={t("global.permission")} />
          <InputElement>
            <SingleSelect
              name={t("study.publicMode")}
              list={publicModeList}
              data={publicMode}
              setValue={(value: string) =>
                setPublicMode(value as StudyPublicMode)
              }
              sx={{ flexGrow: 1, mr: 1 }}
            />
            <MultiSelect
              name={t("global.group")}
              list={groupList}
              data={groups}
              setValue={setGroups}
              sx={{ flexGrow: 1, ml: 1 }}
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

export default CreateStudyModal;
