import { useEffect, useMemo, useState } from "react";
import { isEqual } from "lodash";
import debug from "debug";
import { useSnackbar } from "notistack";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import BasicModal from "../common/BasicModal";
import SingleSelect from "../common/SelectSingle";
import MultiSelect from "../common/SelectMulti";
import FilledTextInput from "../common/FilledTextInput";
import {
  GenericInfo,
  GroupDTO,
  StudyMetadata,
  StudyPublicMode,
} from "../../common/types";
import TextSeparator from "../common/TextSeparator";
import {
  addStudyGroup,
  changePublicMode,
  deleteStudyGroup,
  renameStudy,
  updateStudyMetadata,
} from "../../services/api/study";
import { getGroups } from "../../services/api/user";
import enqueueErrorSnackbar from "../common/ErrorSnackBar";
import TagTextInput from "../common/TagTextInput";
import { scrollbarStyle } from "../../theme";

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
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);

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

  const onSubmit = async () => {
    if (studyName && studyName.replace(/\s+/g, "") !== "") {
      try {
        const sid = study.id;

        // Update study name
        if (initStudyName !== studyName) {
          await renameStudy(sid, studyName);
        }

        // Update tags
        if (tagChanged) {
          await updateStudyMetadata(sid, {
            horizon: study.horizon,
            scenario: study.scenario,
            status: study.status,
            doc: study.doc,
            tags,
          });
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
          t("singlestudy:modifiedStudySuccess", { studyname: studyName }),
          { variant: "success" }
        );
      } catch (e) {
        logErr("Failed to modify study", studyName, e);
        enqueueErrorSnackbar(
          enqueueSnackbar,
          t("singlestudy:modifiedStudyFailed", { studyname: studyName }),
          e as AxiosError
        );
      }
      onClose();
    } else {
      enqueueSnackbar(t("data:emptyName"), { variant: "error" });
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

  return (
    <BasicModal
      title={t("singlestudy:properties")}
      open={open}
      onClose={onClose}
      closeButtonLabel={t("main:cancelButton")}
      actionButtonLabel={t("singlestudy:validate")}
      actionButtonDisabled={!dataChanged}
      onActionButtonClick={onSubmit}
      rootStyle={{
        width: "600px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Box
        width="100%"
        height="350px"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
        p={2}
        boxSizing="border-box"
        sx={{ overflowX: "hidden", overflowY: "auto", ...scrollbarStyle }}
      >
        <Box
          width="100%"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
          boxSizing="border-box"
        >
          <FilledTextInput
            label={`${t("studymanager:studyName")} *`}
            value={studyName}
            onChange={setStudyName}
            sx={{ flexGrow: 1, mr: 2 }}
          />
        </Box>
        <Box
          width="100%"
          display="flex"
          flexDirection="column"
          justifyContent="flex-start"
          alignItems="flex-start"
          boxSizing="border-box"
        >
          <TextSeparator text={t("studymanager:permission")} />
          <Box
            width="100%"
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
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
              data={group}
              setValue={setGroup}
              sx={{ flexGrow: 1, ml: 1 }}
            />
          </Box>
        </Box>
        <Box
          width="100%"
          display="flex"
          flexDirection="column"
          justifyContent="flex-start"
          alignItems="flex-start"
          boxSizing="border-box"
        >
          <TextSeparator text="Metadata" />
          <Box
            width="100%"
            display="flex"
            flexDirection="row"
            justifyContent="flex-start"
            alignItems="center"
          >
            <TagTextInput
              label={`${t("studymanager:enterTag")} *`}
              sx={{ flexGrow: 1, mr: 2 }}
              value={tags}
              onChange={setTags}
              tagList={tagList}
            />
          </Box>
        </Box>
      </Box>
    </BasicModal>
  );
}

export default PropertiesModal;
