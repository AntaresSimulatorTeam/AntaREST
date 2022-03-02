import React, { useEffect, useState } from 'react';
import debug from 'debug';
import { Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { connect, ConnectedProps } from 'react-redux';
import BasicModal from '../common/BasicModal';
import SingleSelect from '../common/SelectSingle';
import MultiSelect from '../common/SelectMulti';
import { AppState } from '../../store/reducers';
import { convertVersions } from '../../services/utils';
import FilledTextInput from '../common/FilledTextInput';
import { GenericInfo, GroupDTO, RoleType, StudyMetadata } from '../../common/types';
import TextSeparator from '../common/TextSeparator';
import { createStudy, getStudyMetadata } from '../../services/api/study';
import { addStudies, initStudiesVersion } from '../../store/study';
import { getGroups } from '../../services/api/user';

const logErr = debug('antares:createstudyform:error');

interface Inputs {
  studyname: string;
  version: number;
}

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
    onActionButtonClick: () => void;
  }
  type PropTypes = PropsFromRedux & OwnProps;

function CreateStudyModal(props: PropTypes) {
  const [t] = useTranslation();
  const { versions, open, addStudy, onClose, onActionButtonClick } = props;
  const versionList = convertVersions(versions || []);
  const tagList: Array<GenericInfo> = []; // Replace by ??
  const [version, setVersion] = useState<string>(versionList[versionList.length - 1].id.toString());
  const [studyName, setStudyName] = useState<string>('');
  const [rightToChange, setRightToChange] = useState<string>('');
  const [group, setGroup] = useState<string>('');
  const [tags, setTags] = useState<Array<string>>([]);
  const [groupList, setGroupList] = useState<Array<GroupDTO>>([]);

  const onSubmit = async () => {
    if (studyName && studyName.replace(/\s+/g, '') !== '' && versionList.length > 0) {
      try {
        let vrs = versionList[versionList.length - 1].id as number;
        if (version) {
          const index = versionList.findIndex((elm) => elm.id.toString() === version);
          if (index >= 0) { vrs = versionList[index].id as number; }
        }
        const sid = await createStudy(studyName, vrs, group !== '' ? [group] : undefined);
        const metadata = await getStudyMetadata(sid);
        addStudy(metadata);
      } catch (e) {
        logErr('Failed to create new study', studyName, e);
      }
    }
    onClose();
  };

  const rightToChangeList: Array<GenericInfo> = [
    { id: RoleType.ADMIN, name: t('settings:adminRole') },
    { id: RoleType.RUNNER, name: t('settings:runnerRole') },
    { id: RoleType.WRITER, name: t('settings:writerRole') },
    { id: RoleType.READER, name: t('settings:readerRole') }];

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
      rootStyle={{ width: '600px', height: '500px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'center', boxSizing: 'border-box' }}
    >
      <Box width="100%" height="100%" display="flex" flexDirection="column" justifyContent="flex-start" alignItems="center" p={2} boxSizing="border-box">
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
              name={t('studymanager:rightToChange')}
              list={rightToChangeList}
              data={rightToChange}
              setValue={setRightToChange}
              sx={{ flexGrow: 1, mr: 1 }}
            />
            <SingleSelect
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
            <MultiSelect
              name={t('studymanager:tag')}
              placeholder={t('studymanager:enterTag')}
              list={tagList}
              data={tags}
              setValue={setTags}
              sx={{ flexGrow: 1 }}
            />
          </Box>
        </Box>
      </Box>
    </BasicModal>
  );
}

export default connector(CreateStudyModal);
