import { useEffect, useState } from "react";
import debug from "debug";
import { useSnackbar } from "notistack";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { connect, ConnectedProps } from "react-redux";
import { usePromise } from "react-use";
import SingleSelect from "../../common/SelectSingle";
import MultiSelect from "../../common/SelectMulti";
import { convertVersions } from "../../../services/utils";
import FilledTextInput from "../../common/FilledTextInput";
import { GenericInfo, GroupDTO, StudyPublicMode } from "../../../common/types";
import TextSeparator from "../../common/TextSeparator";
import { getGroups } from "../../../services/api/user";
import TagTextInput from "../../common/TagTextInput";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../common/dialogs/BasicDialog";
import { Root, ElementContainer, InputElement } from "./style";
import { AppState } from "../../../redux/ducks";
import { createStudy } from "../../../redux/ducks/studies";
import { getStudyVersions } from "../../../redux/selectors";

const logErr = debug("antares:createstudyform:error");

const mapState = (state: AppState) => ({
  versions: getStudyVersions(state),
});

const mapDispatch = {
  addStudy: createStudy,
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  open: boolean;
  onClose: () => void;
}
type PropTypes = PropsFromRedux & OwnProps;

function CreateStudyModal(props: PropTypes) {
  const [t] = useTranslation();
  const { versions, open, addStudy, onClose } = props;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const versionList = convertVersions(versions || []);
  const mounted = usePromise();

  // NOTE: GET TAG LIST FROM BACKEND
  const tagList: Array<string> = [];

  const [version, setVersion] = useState<string>(
    versionList[versionList.length - 1].id.toString()
  );
  const [studyName, setStudyName] = useState<string>("");
  const [publicMode, setPublicMode] = useState<StudyPublicMode>("NONE");
  const [groups, setGroups] = useState<Array<string>>([]);
  const [tags, setTags] = useState<Array<string>>([]);
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);
  const [actionButtonDisabled, setActionButtonDisabled] =
    useState<boolean>(false);

  const onSubmit = async () => {
    setActionButtonDisabled(true);
    if (studyName && studyName.replace(/\s+/g, "") !== "") {
      try {
        await mounted(
          addStudy({
            name: studyName,
            version,
            groups,
            publicMode,
            tags,
          }).unwrap()
        );

        enqueueSnackbar(
          t("studymanager:createStudySuccess", { studyname: studyName }),
          { variant: "success" }
        );
      } catch (e) {
        logErr("Failed to create new study", studyName, e);
        enqueueErrorSnackbar(
          t("studymanager:createStudyFailed", { studyname: studyName }),
          e as AxiosError
        );
      }
      onClose();
    } else {
      enqueueSnackbar(t("data:emptyName"), { variant: "error" });
      setActionButtonDisabled(false);
    }
  };

  const publicModeList: Array<GenericInfo> = [
    { id: "NONE", name: t("singlestudy:nonePublicMode") },
    { id: "READ", name: t("singlestudy:readPublicMode") },
    { id: "EXECUTE", name: t("singlestudy:executePublicMode") },
    { id: "EDIT", name: t("singlestudy:editPublicMode") },
    { id: "FULL", name: t("singlestudy:fullPublicMode") },
  ];

  const init = async () => {
    try {
      const groupRes = await getGroups();
      setGroupList(groupRes);
    } catch (error) {
      logErr(error);
    }
  };

  useEffect(() => {
    init();
  }, []);

  return (
    <BasicDialog
      title={t("studymanager:createNewStudy")}
      open={open}
      onClose={onClose}
      contentProps={{
        sx: { width: "500px", height: "380px", p: 0, overflow: "hidden" },
      }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("main:cancelButton")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={onSubmit}
            disabled={actionButtonDisabled}
          >
            {t("main:create")}
          </Button>
        </>
      }
    >
      <Root>
        <InputElement>
          <FilledTextInput
            label={t("studymanager:studyName")}
            value={studyName}
            onChange={setStudyName}
            sx={{ flexGrow: 1, mr: 2 }}
            required
          />
          <SingleSelect
            name={t("studymanager:version")}
            list={versionList}
            data={version}
            setValue={setVersion}
            sx={{ flexGrow: 1 }}
            required
          />
        </InputElement>
        <ElementContainer>
          <TextSeparator text={t("studymanager:permission")} />
          <InputElement>
            <SingleSelect
              name={t("singlestudy:publicMode")}
              list={publicModeList}
              data={publicMode}
              setValue={(value: string) =>
                setPublicMode(value as StudyPublicMode)
              }
              sx={{ flexGrow: 1, mr: 1 }}
            />
            <MultiSelect
              name={t("studymanager:group")}
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
              label={t("studymanager:enterTag")}
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

export default connector(CreateStudyModal);
