/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { createStyles, makeStyles, Theme, TextField, FormControlLabel, Checkbox, Select, MenuItem, InputLabel, FormControl } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import AddCircleOutlinedIcon from '@material-ui/icons/AddCircleOutlined';
import GenericModal from '../ui/GenericModal';
import { FileStudyTreeConfigDTO, StudyDownloadDTO, StudyDownloadLevelDTO, StudyDownloadType } from '../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '350px',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
  },
  yearsContainer: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
  },
}));

interface PropTypes {
    open: boolean;
    onClose: () => void;
    output: string;
    synthesis: FileStudyTreeConfigDTO | undefined;
    onFilter: (output: string, filter: StudyDownloadDTO) => void;
    onExport: (output: string) => void;
}

const ExportFilterModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, onClose, output, synthesis, onFilter, onExport } = props;
  const [exportChecked, setExportChecked] = useState<boolean>(false);
  const [year, setCurrentYear] = useState<number>();
  const [filter, setFilter] = useState<StudyDownloadDTO>({
    type: StudyDownloadType.AREA,
    level: StudyDownloadLevelDTO.WEEKLY,
    synthesis: false,
    includeClusters: false,
  });

  const onTypeChange = (value: StudyDownloadType): void => {
    setFilter({ ...filter, type: value });
  };

  const onSave = async () => {
    console.log('Save: ', output);
  };
  interface StudyDownloadDTA {
    type: StudyDownloadType;
    years?: Array<number>;
    level: StudyDownloadLevelDTO;
    filterIn?: string;
    filterOut?: string;
    filter?: Array<string>;
    columns?: Array<string>;
    synthesis: boolean;
    includeClusters: boolean;
  }
  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleSave={onSave}
      title={`${t('singlestudy:exportOutput')}: ${output}`}
    >
      <div className={classes.infos}>
        <FormControlLabel
          control={<Checkbox checked={exportChecked} onChange={(e, checked) => setExportChecked(checked)} name="Export output" />}
          label={t('main:export')}
        />
        {!exportChecked && (
        <>
          <FormControl fullWidth>
            <InputLabel id="type-select-label">Type</InputLabel>
            <Select
              labelId="type-select-label"
              id="type-simple-select"
              value={filter.type}
              label="Type"
              onChange={(event, child) => onTypeChange(event.target.value as StudyDownloadType)}
            >
              <MenuItem value={StudyDownloadType.AREA}>{StudyDownloadType.AREA}</MenuItem>
              <MenuItem value={StudyDownloadType.LINK}>{StudyDownloadType.LINK}</MenuItem>
              <MenuItem value={StudyDownloadType.DISTRICT}>{StudyDownloadType.DISTRICT}</MenuItem>
            </Select>
          </FormControl>
          <FormControl>
            <div className={classes.yearsContainer}>
              <TextField
              // labelId="year-select-label"
                id="year-simple-select"
                type="number"
                label="Year"
                value={year}
                onChange={(e) => setCurrentYear(parseInt(e.target.value as string, 10))}
              />
              <AddCircleOutlinedIcon color="secondary" style={{ cursor: 'pointer' }} onClick={() => setFilter({ ...filter, years: year ? filter.years?.concat(year) : filter.years })} />
            </div>

          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="level-select-label">Level</InputLabel>
            <Select
              labelId="level-select-label"
              id="level-simple-select"
              value={filter.level}
              label="Level"
              onChange={(event, child) => setFilter({ ...filter, level: event.target.value as StudyDownloadLevelDTO })}
            >
              <MenuItem value={StudyDownloadLevelDTO.HOURLY}>{StudyDownloadLevelDTO.HOURLY}</MenuItem>
              <MenuItem value={StudyDownloadLevelDTO.DAILY}>{StudyDownloadLevelDTO.DAILY}</MenuItem>
              <MenuItem value={StudyDownloadLevelDTO.WEEKLY}>{StudyDownloadLevelDTO.WEEKLY}</MenuItem>
              <MenuItem value={StudyDownloadLevelDTO.MONTHLY}>{StudyDownloadLevelDTO.MONTHLY}</MenuItem>
              <MenuItem value={StudyDownloadLevelDTO.ANNUAL}>{StudyDownloadLevelDTO.ANNUAL}</MenuItem>
            </Select>
          </FormControl>

          <FormControlLabel
            control={<Checkbox checked={filter.synthesis} onChange={(e, checked) => setFilter({ ...filter, synthesis: checked })} name="Synthesis" />}
            label="Synthesis"
          />
          <FormControlLabel
            control={<Checkbox checked={filter.includeClusters} onChange={(e, checked) => setFilter({ ...filter, includeClusters: checked })} name="Include clusters" />}
            label="Include clusters"
          />
        </>
        )}
      </div>
    </GenericModal>
  );
};

export default ExportFilterModal;
