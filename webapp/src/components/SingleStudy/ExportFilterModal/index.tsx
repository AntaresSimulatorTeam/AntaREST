/* eslint-disable camelcase */
/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, FormControlLabel, Checkbox, Divider } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import _ from 'lodash';
import GenericModal from '../../ui/GenericModal';
import { Area, Set as District, FileStudyTreeConfigDTO, StudyOutputDownloadDTO, StudyOutputDownloadLevelDTO, StudyOutputDownloadType } from '../../../common/types';
import ExportFilter from './ExportFilter';
import CustomSelect from './CustomSelect';
import TagSelect from './TagSelect';

const useStyles = makeStyles((theme: Theme) => createStyles({
  infos: {
    flex: '1',
    width: '350px',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: theme.spacing(2),
    overflowX: 'hidden',
    overflowY: 'auto',
  },
  divider: {
    width: '100%',
    height: '1px',
    backgroundColor: theme.palette.grey[400],
    margin: theme.spacing(5, 0),
  },
}));

interface PropTypes {
    open: boolean;
    onClose: () => void;
    output: string;
    synthesis: FileStudyTreeConfigDTO | undefined;
    onExportFiltered: (output: string, filter: StudyOutputDownloadDTO) => void;
    onExport: (output: string) => void;
}

const ExportFilterModal = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { open, onClose, output, synthesis, onExportFiltered, onExport } = props;
  const [exportChecked, setExportChecked] = useState<boolean>(false);
  const [year, setCurrentYear] = useState<Array<number>>([]);
  const [byYear, setByYear] = useState<{isByYear: boolean; nbYear: number}>({ isByYear: false, nbYear: -1 });
  const [areaList, setAreaList] = useState<{[elm: string]: Area}>({});
  const [districtList, setDistrictList] = useState<{[elm: string]: District}>({});
  const [filter, setFilter] = useState<StudyOutputDownloadDTO>({
    type: StudyOutputDownloadType.AREA,
    level: StudyOutputDownloadLevelDTO.WEEKLY,
    synthesis: false,
    includeClusters: false,
  });

  const typeList: Array<string> = [StudyOutputDownloadType.AREA, StudyOutputDownloadType.LINK, StudyOutputDownloadType.DISTRICT];
  const levelList: Array<string> = [StudyOutputDownloadLevelDTO.HOURLY,
    StudyOutputDownloadLevelDTO.DAILY,
    StudyOutputDownloadLevelDTO.WEEKLY,
    StudyOutputDownloadLevelDTO.MONTHLY,
    StudyOutputDownloadLevelDTO.ANNUAL];

  const onSave = async () => {
    if (exportChecked) {
      onExport(output);
    } else {
      onExportFiltered(output, filter);
    }
    onClose();
  };

  const onTypeChange = (value: Array<string> | string): void => {
    setFilter({ ...filter, type: value as StudyOutputDownloadType });
  };

  const onLevelChange = (value: Array<string> | string): void => {
    setFilter({ ...filter, level: value as StudyOutputDownloadLevelDTO });
  };

  useEffect(() => {
    if (synthesis && output in synthesis?.outputs) {
      const outputs = synthesis.outputs[output];
      setByYear({ isByYear: outputs?.by_year, nbYear: outputs?.nbyears });
      setAreaList(synthesis.areas);
      setDistrictList(synthesis.sets);
    }
  }, [synthesis, output]);

  return (
    <GenericModal
      open={open}
      handleClose={onClose}
      handleAction={onSave}
      actionName={t('main:export')}
      title={`${t('singlestudy:exportOutput')}: ${output}`}
    >
      <div className={classes.infos}>
        <FormControlLabel
          control={<Checkbox checked={exportChecked} onChange={(e, checked) => setExportChecked(checked)} name={t('singlestudy:exportAll')} />}
          label={t('singlestudy:exportAll')}
        />
        {!exportChecked && (
        <>
          <Divider className={classes.divider} />
          <CustomSelect
            fullWidth
            label={t('singlestudy:type')}
            style={{ marginBottom: '16px' }}
            list={typeList.map((elm) => ({ key: elm, value: t(`singlestudy:${elm.toLowerCase()}`) }))}
            value={filter.type}
            onChange={onTypeChange}
          />
          {byYear.isByYear && byYear.nbYear > 0 && (
          <CustomSelect
            fullWidth
            multiple
            label={t('singlestudy:years')}
            style={{ marginBottom: '16px' }}
            list={_.range(byYear.nbYear).map((elm) => ({ key: elm.toString(), value: elm.toString() }))}
            value={year.map((elm) => elm.toString())}
            onChange={(value: Array<string> | string) => setCurrentYear((value as Array<string>).map((elm) => parseInt(elm, 10)))}
          />
          )}
          <CustomSelect
            fullWidth
            label={t('singlestudy:level')}
            style={{ marginBottom: '16px' }}
            list={levelList.map((elm) => ({ key: elm, value: t(`singlestudy:${elm.toLowerCase()}`) }))}
            value={filter.level}
            onChange={onLevelChange}
          />
          <TagSelect
            label={t('singlestudy:columns')}
            values={filter.columns !== undefined ? filter.columns : []}
            onChange={(value: Array<string>) => setFilter({ ...filter, columns: value })}
          />
          <ExportFilter
            type={filter.type}
            areas={areaList}
            sets={districtList}
            filterValue={filter.filter ? filter.filter : []}
            setFilterValue={(elm: Array<string>) => setFilter({ ...filter, filter: elm })}
            filterInValue={filter.filterIn ? filter.filterIn : ''}
            setFilterInValue={(elm: string) => setFilter({ ...filter, filterIn: elm })}
            filterOutValue={filter.filterOut ? filter.filterOut : ''}
            setFilterOutValue={(elm: string) => setFilter({ ...filter, filterOut: elm })}
          />
          <FormControlLabel
            control={<Checkbox checked={filter.synthesis} onChange={(e, checked) => setFilter({ ...filter, synthesis: checked })} name={t('singlestudy:synthesis')} />}
            label={t('singlestudy:synthesis')}
          />
          <FormControlLabel
            control={<Checkbox checked={filter.includeClusters} onChange={(e, checked) => setFilter({ ...filter, includeClusters: checked })} name={t('singlestudy:includeClusters')} />}
            label={t('singlestudy:includeClusters')}
          />
        </>
        )}
      </div>
    </GenericModal>
  );
};

export default ExportFilterModal;
