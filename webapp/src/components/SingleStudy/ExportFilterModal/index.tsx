/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { createStyles, makeStyles, Theme, TextField, FormControlLabel, Checkbox, Select, MenuItem, InputLabel, FormControl, Input } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../ui/GenericModal';
import { Area, Set as District, FileStudyTreeConfigDTO, StudyDownloadDTO, StudyDownloadLevelDTO, StudyDownloadType } from '../../../common/types';
import _ from 'lodash';
import MultipleSelect from './MultipleSelect';
import SingleSelect from './SingleSelect';
import ExportFilter from './ExportFilter';

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
  const [year, setCurrentYear] = useState<Array<number>>([]);
  const [byYear, setByYear] = useState<{isByYear: boolean, nbYear: number}>({ isByYear: false, nbYear: -1 });
  const [areaList, setAreaList] = useState<{[elm: string]: Area}>({});
  const [districtList, setDistrictList] = useState<{[elm: string]: District}>({});
  const [filter, setFilter] = useState<StudyDownloadDTO>({
    type: StudyDownloadType.AREA,
    level: StudyDownloadLevelDTO.WEEKLY,
    synthesis: false,
    includeClusters: false,
  });

  const typeList: Array<string> = [StudyDownloadType.AREA, StudyDownloadType.LINK, StudyDownloadType.DISTRICT];
  const levelList: Array<string> = [StudyDownloadLevelDTO.HOURLY,
                      StudyDownloadLevelDTO.DAILY,
                      StudyDownloadLevelDTO.WEEKLY,
                      StudyDownloadLevelDTO.MONTHLY,
                      StudyDownloadLevelDTO.ANNUAL]


  const onSave = async () => {
    console.log('Save: ', output);
  };

  useEffect(() => {
    if(synthesis && output in synthesis?.outputs) {
      const outputs = synthesis.outputs[output];
      setByYear( { isByYear: outputs?.by_year, nbYear: outputs?.nbyears } );
      setAreaList(synthesis.areas);
      setDistrictList(synthesis.sets);
    }
  }, [synthesis, output])

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
          <SingleSelect fullWidth 
                      label="Type"
                      style={{ marginBottom: '16px' }}
                      list={typeList}
                      value={filter.type}
                      onChange={(value: string) => setFilter({ ...filter, type: value as StudyDownloadType })} />
          {byYear.isByYear && byYear.nbYear > 0 &&
          <MultipleSelect fullWidth label="Year" list={_.range(byYear.nbYear).map(elm => elm.toString())} value={year.map(elm => elm.toString())} onChange={(value: Array<string>) => setCurrentYear(value.map(elm => parseInt(elm,10)))} />}
          <SingleSelect fullWidth 
                      label="Level"
                      style={{ marginBottom: '16px' }}
                      list={levelList}
                      value={filter.level}
                      onChange={(value: string) => setFilter({ ...filter, level: value as StudyDownloadLevelDTO })} />
          <ExportFilter
              type={filter.type}
              areas={areaList}
              sets={districtList}
              filterValue={filter.filter ? filter.filter : []}
              setFilterValue={(elm: Array<string>) => setFilter({ ...filter, filter: elm  })}
              filterInValue={filter.filterIn ? filter.filterIn : ''}
              setFilterInValue={(elm: string) => setFilter({ ...filter, filterIn: elm  })}
              filterOutValue={filter.filterOut ? filter.filterOut : ''}
              setFilterOutValue={(elm: string) => setFilter({ ...filter, filterOut: elm  })} />
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
