/* eslint-disable @typescript-eslint/camelcase */
import React, { useEffect, useState } from 'react';
import { Chip, createStyles, makeStyles, TextField, Theme, Typography } from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';
import AddCircleOutlinedIcon from '@material-ui/icons/AddCircleOutlined';
import { Area, Set, StudyOutputDownloadType } from '../../../common/types';
import CustomSelect from './CustomSelect';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: 0,
  },
  linkContainer: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    boxSizing: 'border-box',
  },
  singleLink: {
    alignItems: 'flex-end',
    marginBottom: theme.spacing(2),
  },
  linkFilter: {
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
    padding: 0,
    width: '250px',
    overflow: 'hidden',
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
    marginTop: theme.spacing(1),
    margin: 0,
  },
  chip: {
    margin: theme.spacing(0.5),
  },
  addIcon: {
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 1),
    cursor: 'pointer',
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
    type: StudyOutputDownloadType;
    areas: {[elm: string]: Area};
    sets: {[elm: string]: Set};
    filterValue: Array<string>;
    setFilterValue: (elm: Array<string>) => void;
    filterInValue: string;
    setFilterInValue: (elm: string) => void;
    filterOutValue: string;
    setFilterOutValue: (elm: string) => void;
}

const SingleLinkElement = (props: {globalFilter?: boolean; label: string; areas: Array<string>; onChange: (value: string) => void}) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { globalFilter, label, areas, onChange } = props;
  const [link, setLink] = useState<FilterLink>({ area1: '', area2: '' });

  const onSelectChange = (id: number, elm: string): void => {
    let { area1, area2 } = link;
    if (id === 0) {
      area1 = elm;
      setLink({ ...link, area1: elm });
    } else {
      area2 = elm;
      setLink({ ...link, area2: elm });
    }
    onChange(`${area1}^${area2}`);
  };
  return (
    <div className={clsx(classes.linkContainer, classes.singleLink)}>
      <Typography className={classes.linkLabel}>
        {label}
        :
      </Typography>
      {
          globalFilter === true ? (
            <div className={classes.linkFilter}>
              <CustomSelect
                label={`${t('singlestudy:area')} 1`}
                list={areas.map((elm) => ({ key: elm, value: elm }))}
                value={link.area1}
                onChange={(elm: Array<string> | string) => onSelectChange(0, elm as string)}
                style={{ marginLeft: '5px', marginRight: '5px', width: '50%' }}
              />
              <CustomSelect
                style={{ width: '50%' }}
                label={`${t('singlestudy:area')}2`}
                list={areas.map((elm) => ({ key: elm, value: elm }))}
                value={link.area2}
                onChange={(elm: Array<string> | string) => onSelectChange(1, elm as string)}
              />
            </div>
          ) : (
            <div className={classes.linkFilter}>
              <TextField label={`${t('singlestudy:area')} 1`} value={link.area1} onChange={(event) => onSelectChange(0, event.target.value)} style={{ marginLeft: '5px', marginRight: '5px', width: '100%' }} />
              <TextField label={`${t('singlestudy:area')} 2`} value={link.area2} onChange={(event) => onSelectChange(1, event.target.value)} style={{ width: '100%' }} />
            </div>
          )}
    </div>
  );
};

SingleLinkElement.defaultProps = {
  globalFilter: false,
};

const MultipleLinkElement = (props: {label: string; areas: Array<string>; values: Array<string>; onChange: (value: Array<string>) => void}) => {
  const classes = useStyles();
  const { label, areas, values, onChange } = props;
  const [currentLink, setCurrentLink] = useState<string>('');

  const onAddLink = (): void => {
    if (values.findIndex((elm) => elm === currentLink) < 0 && currentLink !== '') {
      onChange(values.concat(currentLink));
    }
  };

  return (
    <div className={classes.root} style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div className={classes.linkContainer} style={{ alignItems: 'center' }}>
        <SingleLinkElement globalFilter label={label} areas={areas} onChange={setCurrentLink} />
        <AddCircleOutlinedIcon className={classes.addIcon} onClick={onAddLink} />
      </div>
      {values.length > 0 && (
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
      )}
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
        case StudyOutputDownloadType.AREA:
          res = Object.keys(areas);
          break;

        case StudyOutputDownloadType.DISTRICT:
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
    <>
      {type !== StudyOutputDownloadType.LINK ? (
        <div className={classes.root}>
          <CustomSelect
            fullWidth
            multiple
            label={t('singlestudy:filter')}
            list={areasOrDistrictsList.map((elm) => ({ key: elm, value: elm }))}
            value={filterValue}
            onChange={(elm: Array<string> | string) => setFilterValue(elm as Array<string>)}
            style={{ marginBottom: '16px' }}
          />
          <TextField label={t('singlestudy:filterIn')} value={filterInValue} onChange={(event) => setFilterInValue(event.target.value)} style={{ marginBottom: '16px', width: '100%' }} />
          <TextField label={t('singlestudy:filterOut')} value={filterOutValue} onChange={(event) => setFilterOutValue(event.target.value)} style={{ marginBottom: '16px', width: '100%' }} />
        </div>
      ) : (
        <div className={classes.root}>
          <MultipleLinkElement label={t('singlestudy:filter')} areas={Object.keys(areas)} values={filterValue} onChange={setFilterValue} />
          <SingleLinkElement label={t('singlestudy:filterIn')} areas={Object.keys(areas)} onChange={setFilterInValue} />
          <SingleLinkElement label={t('singlestudy:filterOut')} areas={Object.keys(areas)} onChange={setFilterOutValue} />
        </div>
      )}
    </>

  );
};

export default ExportFilter;
