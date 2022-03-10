import React, { useEffect, useState } from 'react';
import debug from 'debug';
import { useSnackbar } from 'notistack';
import { Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { AxiosError } from 'axios';
import { connect, ConnectedProps } from 'react-redux';
import BasicModal from '../common/BasicModal';
import SingleSelect from '../common/SelectSingle';
import MultiSelect from '../common/SelectMulti';
import { AppState } from '../../store/reducers';
import { convertVersions } from '../../services/utils';
import FilledTextInput from '../common/FilledTextInput';
import { GenericInfo, GroupDTO, StudyMetadata, StudyPublicMode } from '../../common/types';
import TextSeparator from '../common/TextSeparator';
import { changePublicMode, createStudy, getStudyMetadata, updateStudyMetadata } from '../../services/api/study';
import { addStudies, initStudiesVersion } from '../../store/study';
import { getGroups } from '../../services/api/user';
import enqueueErrorSnackbar from '../common/ErrorSnackBar';
import TagTextInput from '../common/TagTextInput';
import { scrollbarStyle } from '../../theme';

const logErr = debug('antares:createstudyform:error');

const mapState = (state: AppState) => ({
  versions: state.study.versionList,
});

const mapDispatch = ({
  addStudy: (study: StudyMetadata) => addStudies([study]),
  loadVersions: initStudiesVersion,
});

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
  const versionList = convertVersions(versions || []);

  // NOTE: GET TAG LIST FROM BACKEND
  const tagList: Array<string> = [];

  const [version, setVersion] = useState<string>(versionList[versionList.length - 1].id.toString());
  const [studyName, setStudyName] = useState<string>('');
  const [publicMode, setPublicMode] = useState<StudyPublicMode>('NONE');
  const [group, setGroup] = useState<Array<string>>([]);
  const [tags, setTags] = useState<Array<string>>([]);
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);

  const onSubmit = async () => {
    if (studyName && studyName.replace(/\s+/g, '') !== '') {
      try {
        let vrs = versionList[versionList.length - 1].id as number;
        if (version) {
          const index = versionList.findIndex((elm) => elm.id.toString() === version);
          if (index >= 0) { vrs = versionList[index].id as number; }
        }
        const sid = await createStudy(studyName, vrs, group);
        const metadata = await getStudyMetadata(sid);
        await changePublicMode(sid, publicMode);
        if (tags.length > 0) await updateStudyMetadata(sid, { tags });
        addStudy(metadata);
        enqueueSnackbar(t('studymanager:createStudySuccess', { studyname: studyName }), { variant: 'success' });
      } catch (e) {
        logErr('Failed to create new study', studyName, e);
        enqueueErrorSnackbar(enqueueSnackbar, t('studymanager:createStudyFailed', { studyname: studyName }), e as AxiosError);
      }
      onClose();
    } else {
      enqueueSnackbar(t('data:emptyName'), { variant: 'error' });
    }
  };

  const publicModeList: Array<GenericInfo> = [
    { id: 'NONE', name: t('singlestudy:nonePublicMode') },
    { id: 'READ', name: t('singlestudy:readPublicMode') },
    { id: 'EXECUTE', name: t('singlestudy:executePublicMode') },
    { id: 'EDIT', name: t('singlestudy:editPublicMode') },
    { id: 'FULL', name: t('singlestudy:fullPublicMode') }];

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
    <BasicModal
      title={t('studymanager:createNewStudy')}
      open={open}
      onClose={onClose}
      closeButtonLabel={t('main:cancelButton')}
      actionButtonLabel={t('main:create')}
      onActionButtonClick={onSubmit}
      rootStyle={{ width: '600px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center', boxSizing: 'border-box' }}
    >
      <Box width="100%" height="400px" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" p={2} boxSizing="border-box" sx={{ overflowX: 'hidden', overflowY: 'auto', ...scrollbarStyle }}>
        <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center" boxSizing="border-box">
          <FilledTextInput
            label={`${t('studymanager:studyName')} *`}
            value={studyName}
            onChange={setStudyName}
            sx={{ flexGrow: 1, mr: 2 }}
          />
          <SingleSelect
            name={`${t('studymanager:version')} *`}
            list={versionList}
            data={version}
            setValue={setVersion}
          />
        </Box>
        <Box width="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start" boxSizing="border-box">
          <TextSeparator text={t('studymanager:permission')} />
          <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <SingleSelect
              name={t('singlestudy:publicMode')}
              list={publicModeList}
              data={publicMode}
              setValue={(value: string) => setPublicMode(value as StudyPublicMode)}
              sx={{ flexGrow: 1, mr: 1 }}
            />
            <MultiSelect
              name={t('studymanager:group')}
              list={groupList}
              data={group}
              setValue={setGroup}
              sx={{ flexGrow: 1, ml: 1 }}
            />
          </Box>
        </Box>
        <Box width="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="flex-start" boxSizing="border-box">
          <TextSeparator text="Metadata" />
          <Box width="100%" display="flex" flexDirection="row" justifyContent="flex-start" alignItems="center">
            <TagTextInput
              label={`${t('studymanager:enterTag')} *`}
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

export default connector(CreateStudyModal);
