import React, { useState } from 'react';
import { Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { connect, ConnectedProps } from 'react-redux';
import BasicModal from '../common/BasicModal';
import SingleSelect from '../common/SelectSingle';
import MultiSelect from '../common/SelectMulti';
import { AppState } from '../../store/reducers';
import { convertVersions } from '../../services/utils';
import FilledTextInput from '../common/FilledTextInput';
import { GenericInfo } from '../../common/types';
import TextSeparator from '../common/TextSeparator';

const mapState = (state: AppState) => ({
  versions: state.study.versionList,
});

const connector = connect(mapState);
  type PropsFromRedux = ConnectedProps<typeof connector>;
  interface OwnProps {
    open: boolean;
    onClose: () => void;
    onActionButtonClick: () => void;
  }
  type PropTypes = PropsFromRedux & OwnProps;

function CreateStudyModal(props: PropTypes) {
  const [t] = useTranslation();
  const { versions, open, onClose, onActionButtonClick } = props;
  const versionList = convertVersions(versions || []);
  const rightToChangeList: Array<GenericInfo> = []; // Replace by ??
  const groupList: Array<GenericInfo> = []; // Replace by ??
  const tagList: Array<GenericInfo> = []; // Replace by ??
  const [version, setVersion] = useState<string>();
  const [studyName, setStudyName] = useState<string>('');
  const [rightToChange, setRightToChange] = useState<string>('');
  const [group, setGroup] = useState<string>('');
  const [tags, setTags] = useState<Array<string>>([]);

  return (
    <BasicModal
      title={t('studymanager:createNewStudy')}
      open={open}
      onClose={onClose}
      closeButtonLabel={t('main:cancelButton')}
      actionButtonLabel={t('main:create')}
      onActionButtonClick={onActionButtonClick}
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
