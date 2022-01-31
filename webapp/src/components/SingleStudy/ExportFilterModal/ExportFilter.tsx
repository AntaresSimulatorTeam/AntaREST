/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { Chip, createStyles, makeStyles, Theme, Typography } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import AddCircleOutlinedIcon from '@material-ui/icons/AddCircleOutlined';
import { Area, Set, StudyDownloadType } from '../../../common/types';
import MultipleSelect from './MultipleSelect';
import SingleSelect from './SingleSelect';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: 0,
  },
  singleLink: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
    padding: 0,
    marginBottom: theme.spacing(1),
  },
  linkLabel: {
    height: '100%',
    marginRight: '5px',
  },
  filterLinkContainer: {
    display: 'flex',
    border: 0,
    backgroundColor: '#00000000',
    justifyContent: 'center',
    flexWrap: 'wrap',
    listStyle: 'none',
    padding: theme.spacing(0.5),
    margin: 0,
  },
  chip: {
    margin: theme.spacing(0.5),
  },
  addIcon: {
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 1),
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
}));

interface FilterLink {
  area1: string;
  area2: string;
}

interface PropTypes {
    type: StudyDownloadType;
    areas: {[elm: string]: Area};
    sets: {[elm: string]: Set};
    filterValue: Array<string>;
    setFilterValue: (elm: Array<string>) => void;
    filterInValue: string;
    setFilterInValue: (elm: string) => void;
    filterOutValue: string;
    setFilterOutValue: (elm: string) => void;
}

const SingleLinkElement = (props: {label: string; areas: Array<string>; onChange: (value: string) => void}) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { label, areas, onChange } = props;
  const [link, setLink] = useState<FilterLink>({ area1: '', area2: '' });

  const onSelectChange = (id: number, elm: string): void => {
    let { area1, area2 } = link;
    if (elm !== '') {
      if (id === 0) {
        area1 = elm;
        setLink({ ...link, area1: elm });
      } else {
        area2 = elm;
        setLink({ ...link, area2: elm });
      }
      if (area1 !== '' && area2 !== '') onChange(`${area1}>${area2}`);
    }
  };
  return (
    <div className={classes.singleLink}>
      <Typography className={classes.linkLabel}>
        {label}
        :
      </Typography>
      <div className={classes.singleLink} style={{ width: 'auto', flex: 1, alignItems: 'center', height: '40px' }}>
        <SingleSelect fullWidth label={`${t('singlestudy:area')} 1`} list={areas} value={link.area1} onChange={(elm) => onSelectChange(0, elm)} style={{ marginLeft: '5px', marginRight: '5px' }} />
        <SingleSelect fullWidth label={`${t('singlestudy:area')}2`} list={areas} value={link.area2} onChange={(elm) => onSelectChange(1, elm)} />
      </div>
    </div>
  );
};

const MultipleLinkElement = (props: {label: string; areas: Array<string>; values: Array<string>; onChange: (value: Array<string>) => void}) => {
  const classes = useStyles();
  const { label, areas, values, onChange } = props;
  const [currentLink, setCurrentLink] = useState<string>('');

  const onAddLink = (): void => {
    // const tmp: Array<string> = [...value];
    if (values.findIndex((elm) => elm === currentLink) < 0 && currentLink !== '') {
      onChange(values.concat(currentLink));
      console.log(values.concat(currentLink));
    }
  };

  return (
    <div className={classes.root} style={{ marginBottom: 0 }}>
      <div className={classes.singleLink} style={{ alignItems: 'center' }}>
        <SingleLinkElement label={label} areas={areas} onChange={setCurrentLink} />
        <AddCircleOutlinedIcon className={classes.addIcon} onClick={onAddLink} />
      </div>
      <ul className={classes.filterLinkContainer}>
        {values.map((elm) => (
          <li key={elm}>
            <Chip
              label={elm}
              onDelete={() => onChange(values.filter((link) => link !== elm))}
              className={classes.chip}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

const ExportFilter = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { type, areas, sets, filterValue, filterInValue, filterOutValue, setFilterValue, setFilterInValue, setFilterOutValue } = props;
  const [areasOrDistrictsList, setAreasOrDistrictsList] = useState<Array<string>>([]);

  useEffect(() => {
    const getAreasOrDistrictsList = (): Array<string> => {
      let res: Array<string> = [];
      switch (type) {
        case StudyDownloadType.AREA:
          res = Object.keys(areas);
          break;

        case StudyDownloadType.DISTRICT:
          res = Object.keys(sets);
          break;

        default:
          break;
      }
      return res;
    };
    setAreasOrDistrictsList(getAreasOrDistrictsList());
  }, [areas, sets, type]);

  return (
    <div className={classes.root}>
      {type !== StudyDownloadType.LINK ? (
        <>
          <MultipleSelect fullWidth label={t('singlestudy:filter')} list={areasOrDistrictsList} value={filterValue} onChange={setFilterValue} style={{ marginBottom: '16px' }} />
          <SingleSelect fullWidth label={t('singlestudy:filterIn')} list={areasOrDistrictsList} value={filterInValue} onChange={setFilterInValue} style={{ marginBottom: '16px' }} />
          <SingleSelect fullWidth label={t('singlestudy:filterOut')} list={areasOrDistrictsList} value={filterOutValue} onChange={setFilterOutValue} style={{ marginBottom: '16px' }} />
        </>
      ) : (
        <>
          <MultipleLinkElement label={t('singlestudy:filter')} areas={Object.keys(areas)} values={filterValue} onChange={setFilterValue} />
          <SingleLinkElement label={t('singlestudy:filterIn')} areas={Object.keys(areas)} onChange={setFilterInValue} />
          <SingleLinkElement label={t('singlestudy:filterOut')} areas={Object.keys(areas)} onChange={setFilterOutValue} />
        </>
      )}
    </div>

  );
};

export default ExportFilter;
