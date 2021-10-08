// @flow
import React, { CSSProperties, useState } from 'react';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';
import { DraggableProvided } from 'react-beautiful-dnd';
import ReactJson, { InteractionProps } from 'react-json-view';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import { Accordion, AccordionDetails, AccordionSummary, CircularProgress, createStyles, makeStyles, Theme, Typography } from '@material-ui/core';
import ExpandMore from '@material-ui/icons/ExpandMore';
import SaveOutlinedIcon from '@material-ui/icons/SaveOutlined';
import CloudDownloadOutlinedIcon from '@material-ui/icons/CloudDownloadOutlined';
import InfoIcon from '@material-ui/icons/Info';
import { CommandItem } from '../CommandTypes';
import CommandImportButton from './CommandImportButton';
import { CommandResultDTO } from '../../../../common/types';
import LogModal from '../../../ui/LogModal';

const useStyles = makeStyles((theme: Theme) => createStyles({
  item: {
    boxSizing: 'border-box',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    width: '100%',
    height: 'auto',
    userSelect: 'none',
    maxWidth: '800px',
  },
  itemContainer: {
    display: 'flex',
    justifyContent: 'center',
  },
  onTopVisible: {
    zIndex: 10000,
  },
  onTopInvisible: {
    zIndex: 9999,
    transition: '1s',
  },
  normalItem: {
    flex: 1,
    border: `1px solid ${theme.palette.primary.main}`,
    margin: theme.spacing(0, 0.2),
    boxSizing: 'border-box',
  },
  draggingListItem: {
    flex: 1,
    borderColor: theme.palette.secondary.main,
    boxShadow: `0px 0px 2px rgb(8, 58, 30), 0px 0px 10px ${theme.palette.secondary.main}`,
  },
  deleteIcon: {
    flex: '0 0 24px',
    color: theme.palette.error.light,
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    cursor: 'pointer',
    '&:hover': {
      color: theme.palette.error.main,
    },
  },
  infos: {
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    boxSizing: 'border-box',
  },
  details: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
  },
  header: {
    width: '100%',
    height: '50px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
    boxSizing: 'border-box',
    padding: theme.spacing(0, 1),
  },
  headerIcon: {
    width: '24px',
    height: 'auto',
    cursor: 'pointer',
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 0.5),
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  loadingIcon: {
    width: '24px',
    height: '24px',
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 0.5),
  },
  successIconColor: {
    color: theme.palette.success.main,
    '&:hover': {
      color: theme.palette.success.dark,
    },
  },
  errorIconColor: {
    color: theme.palette.error.main,
    '&:hover': {
      color: theme.palette.error.dark,
    },
  },
  json: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    zIndex: 999, // for json edition modal to be up everything else
    maxHeight: '400px',
    overflow: 'scroll',
  },
}));

interface StyleType {
    provided: DraggableProvided;
    style: CSSProperties;
    isDragging: boolean;
}
function getStyle({ provided, style, isDragging }: StyleType) {
  // If you don't want any spacing between your items
  // then you could just return this.
  // I do a little bit of magic to have some nice visual space
  // between the row items
  const combined = {
    ...style,
    ...provided.draggableProps.style,
  };

  const marginBottom = 8;
  const withSpacing = {
    ...combined,
    height: isDragging ? combined.height : (combined.height as number) - marginBottom,
    marginBottom,
  };
  return withSpacing;
}

interface PropsType {
    provided: DraggableProvided;
    item: CommandItem;
    style: CSSProperties;
    isDragging: boolean;
    index: number;
    generationStatus: boolean;
    generationIndex: number;
    onDelete: (index: number) => void;
    onArgsUpdate: (index: number, json: object) => void;
    onSave: (index: number) => void;
    onCommandImport: (index: number, json: object) => void;
    onCommandExport: (index: number) => void;
}

function Item({ provided, item, style, isDragging, index, generationStatus, generationIndex, onDelete, onArgsUpdate, onSave, onCommandImport, onCommandExport }: PropsType) {
  const classes = useStyles();
  const [t] = useTranslation();
  const [jsonData, setJsonData] = useState<object>(item.args);
  const [isExpanded, setExpanded] = useState<boolean>(false);
  const [logModalOpen, setLogModalOpen] = useState<boolean>(false);

  const updateJson = (e: InteractionProps) => {
    setJsonData(e.updated_src);
    onArgsUpdate(index, e.updated_src);
  };

  const onImport = async (json: object) => {
    // eslint-disable-next-line dot-notation
    // setJsonData((json as any)['args']);
    const oldJson = { ...jsonData };
    try {
      setJsonData(json as any);
      await onCommandImport(index, json);
    } catch (e) {
      setJsonData(oldJson);
    }
  };

  const itemElements = () => {
    if (generationStatus && generationIndex === index) {
      return <CircularProgress color="primary" style={{ width: '24px', height: '24px', margin: '0px 16px' }} />;
    }
    return (
      <>
        {!generationStatus && <DeleteIcon className={classes.deleteIcon} onClick={() => onDelete(index)} />}
        {item.results !== undefined && <InfoIcon className={clsx(classes.headerIcon, (item.results as CommandResultDTO).success ? classes.successIconColor : classes.errorIconColor)} onClick={() => setLogModalOpen(true)} /> }
      </>
    );
  };

  return (
    <div
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.draggableProps}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.dragHandleProps}
      ref={provided.innerRef}
      style={getStyle({ provided, style, isDragging })}
      className={isExpanded ? clsx(classes.itemContainer, classes.onTopVisible) : clsx(classes.itemContainer, classes.onTopInvisible)}
    >
      <div className={classes.item}>
        <Accordion
          className={isDragging ? classes.draggingListItem : classes.normalItem}
        >
          <AccordionSummary
            expandIcon={<ExpandMore />}
            aria-controls="panel1a-content"
            id="panel1a-header"
            onClick={() => setExpanded(!isExpanded)}
          >
            <div className={classes.infos}>
              <Typography color="primary" style={{ fontSize: '0.9em' }}>{item.action}</Typography>
              <Typography style={{ fontSize: '0.8em', color: 'gray' }}>{item.id}</Typography>
            </div>
          </AccordionSummary>
          <AccordionDetails className={classes.details}>
            <div className={classes.details}>
              <div className={classes.header}>
                {item.updated && <SaveOutlinedIcon className={classes.headerIcon} onClick={() => onSave(index)} />}
                {!generationStatus && <CommandImportButton onImport={onImport} /> }
                {!generationStatus && <CloudDownloadOutlinedIcon className={classes.headerIcon} onClick={() => onCommandExport(index)} />}
              </div>
              <div className={classes.json}>
                <ReactJson src={jsonData} onEdit={!generationStatus ? updateJson : undefined} onDelete={!generationStatus ? updateJson : undefined} onAdd={!generationStatus ? updateJson : undefined} />
              </div>
            </div>
          </AccordionDetails>
        </Accordion>
        <div style={{ height: '100%', width: '80px', display: 'flex', justifyContent: 'flex-start', alignItems: 'center' }}>
          {itemElements()}
        </div>
      </div>
      {
        item.results !== undefined && (
        <LogModal
          isOpen={logModalOpen}
          title={t('singlestudy:taskLog')}
          content={item.results.message}
          close={() => setLogModalOpen(false)}
          style={{ width: '400px', height: '200px' }}
        />
        )}
    </div>
  );
}

export default Item;
