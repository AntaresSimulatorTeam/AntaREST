import React, { useCallback, useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme, Typography } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { DropResult } from 'react-beautiful-dnd';
import QueueIcon from '@material-ui/icons/Queue';
import CloudDownloadOutlinedIcon from '@material-ui/icons/CloudDownloadOutlined';
import PowerIcon from '@material-ui/icons/Power';
import { connect, ConnectedProps } from 'react-redux';
import { CommandItem, JsonCommandItem } from './CommandTypes';
import CommandListView from './DraggableCommands/CommandListView';
import { reorder, fromCommandDTOToCommandItem, fromCommandDTOToJsonCommand, exportJson } from './utils';
import { appendCommand, deleteCommand, getCommand, getCommands, moveCommand, updateCommand, replaceCommands, applyCommands } from '../../../services/api/variant';
import AddCommandModal from './AddCommandModal';
import { CommandDTO, WSEvent, WSMessage, CommandResultDTO } from '../../../common/types';
import CommandImportButton from './DraggableCommands/CommandImportButton';
import { addListener, removeListener } from '../../../ducks/websockets';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    flex: 1,
    height: '98%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflowY: 'hidden',
  },
  header: {
    width: '100%',
    height: '80px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  body: {
    width: '100%',
    maxHeight: '90%',
    minHeight: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    overflow: 'auto',
    boxSizing: 'border-box',
  },
  addButton: {
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  headerIcon: {
    width: '24px',
    height: 'auto',
    cursor: 'pointer',
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 3),
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  loadingText: {
    backgroundColor: theme.palette.action.selected,
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    margin: theme.spacing(0, 3),
  },
}));

interface OwnTypes {
    studyId: string;
}

const mapState = () => ({
});

const mapDispatch = ({
  addWsListener: addListener,
  removeWsListener: removeListener,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnTypes;

const EditionView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { studyId, addWsListener, removeWsListener } = props;
  const [openAddCommandModal, setOpenAddCommandModal] = useState<boolean>(false);
  const [generationStatus, setGenerationStatus] = useState<boolean>(false);
  const [generationTaskId, setGenerationTaskId] = useState<string>('');
  const [currentCommandGenerationIndex, setCurrentCommandGenerationIndex] = useState<number>(0);
  const [commands, setCommands] = useState<Array<CommandItem>>([]);

  const onDragEnd = async ({ destination, source }: DropResult) => {
    // dropped outside the list
    if (!destination) return;
    const oldCommands = commands.concat([]);
    try {
      const elm = commands[source.index];
      const newItems = reorder(commands, source.index, destination.index);
      setCommands(newItems);
      await moveCommand(studyId, (elm.id as string), destination.index);
      enqueueSnackbar(t('variants:moveSuccess'), { variant: 'success' });
    } catch (e) {
      setCommands(oldCommands);
      enqueueSnackbar(t('variants:moveError'), { variant: 'error' });
    }
  };

  const onSave = async (index: number) => {
    try {
      const elm = commands[index];
      if (elm.updated) {
        await updateCommand(studyId, (elm.id as string), elm);
        let tmpCommand: Array<CommandItem> = [];
        tmpCommand = tmpCommand.concat(commands);
        tmpCommand[index].updated = false;
        setCommands(tmpCommand);
        enqueueSnackbar(t('variants:saveSuccess'), { variant: 'success' });
      }
    } catch (e) {
      enqueueSnackbar(t('variants:saveError'), { variant: 'error' });
    }
  };

  const onDelete = async (index: number) => {
    try {
      const elm = commands[index];
      await deleteCommand(studyId, (elm.id as string));
      setCommands((commandList) => commandList.filter((item, idx) => idx !== index));
      enqueueSnackbar(t('variants:deleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:deleteError'), { variant: 'error' });
    }
  };

  const onNewCommand = async (action: string) => {
    try {
      const elmDTO: CommandDTO = { action, args: {} };
      const newId = await appendCommand(studyId, elmDTO);
      setCommands(commands.concat([{ ...elmDTO, id: newId, updated: false }]));
      enqueueSnackbar(t('variants:addSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:addError'), { variant: 'error' });
    }
  };

  const onArgsUpdate = (index: number, args: object) => {
    let tmpCommand: Array<CommandItem> = [];
    tmpCommand = tmpCommand.concat(commands);
    tmpCommand[index].args = { ...args };
    tmpCommand[index].updated = true;
    setCommands(tmpCommand);
  };

  const onCommandImport = async (index: number, json: object) => {
    try {
      let tmpCommand: Array<CommandItem> = [];
      tmpCommand = tmpCommand.concat(commands);
      const elm = tmpCommand[index];
      // eslint-disable-next-line dot-notation
      elm.args = { ...json };
      elm.updated = false;
      await updateCommand(studyId, (elm.id as string), elm);
      setCommands(tmpCommand);
      enqueueSnackbar(t('variants:importSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:importError'), { variant: 'error' });
    }
  };

  const onCommandExport = async (index: number) => {
    try {
      const elm = await getCommand(studyId, commands[index].id as string);
      exportJson({ action: elm.action, args: elm.args }, `${elm.id}_command.json`);
    } catch (e) {
      enqueueSnackbar(t('variants:exportError'), { variant: 'error' });
    }
  };

  const onGlobalExport = async () => {
    try {
      const items = await getCommands(studyId);
      exportJson(fromCommandDTOToJsonCommand(items), `${studyId}_commands.json`);
    } catch (e) {
      enqueueSnackbar(t('variants:exportError'), { variant: 'error' });
    }
  };

  const onGlobalImport = async (json: object) => {
    try {
      const globalJson: Array<JsonCommandItem> = (json as Array<JsonCommandItem>);
      await replaceCommands(studyId, globalJson);

      const dtoItems = await getCommands(studyId);
      setCommands(fromCommandDTOToCommandItem(dtoItems));
      enqueueSnackbar(t('variants:importSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:importError'), { variant: 'error' });
    }
  };

  const onGeneration = async () => {
    try {
      // Get commands
      const dtoItems = await getCommands(studyId);
      setCommands(fromCommandDTOToCommandItem(dtoItems));
      setCurrentCommandGenerationIndex(0);
      // Launch generation task
      const generationTask = await applyCommands(studyId);
      setGenerationTaskId(generationTask);
      setGenerationStatus(true);
      enqueueSnackbar(t('variants:launchGenerationSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:launchGenerationError'), { variant: 'error' });
    }
  };

  const listen = useCallback(async (ev: WSMessage) => {
    const commandResult = ev.payload as CommandResultDTO;
    console.log('RESULTS: ', commandResult);
    if (studyId === commandResult.study_id) {
      let tmpCommand: Array<CommandItem> = [];
      tmpCommand = tmpCommand.concat(commands);
      console.log('ELEMENT AT: ', tmpCommand[currentCommandGenerationIndex]);
      const index = tmpCommand.findIndex((item) => item.id === commandResult.id);
      console.log('INDEX:', index);
      switch (ev.type) {
        case WSEvent.STUDY_VARIANT_GENERATION_COMMAND_RESULT:
          tmpCommand[index].results = commandResult;
          if (currentCommandGenerationIndex === commands.length - 1) {
            setGenerationStatus(false);
            setGenerationTaskId('');
          }
          setCurrentCommandGenerationIndex((currentCommandGenerationIndex + 1) % commands.length);
          setCommands(tmpCommand);
          break;
        default:
          break;
      }
    }
  }, [commands, currentCommandGenerationIndex, studyId]);

  useEffect(() => {
    const init = async () => {
      try {
        const dtoItems = await getCommands(studyId);
        setCommands(fromCommandDTOToCommandItem(dtoItems));
      } catch (e) {
        enqueueSnackbar(t('variants:fetchCommandError'), { variant: 'error' });
      }
    };

    addWsListener(listen);
    init();
    return () => removeWsListener(listen);
  }, [addWsListener, enqueueSnackbar, listen, removeWsListener, studyId, t]);

  return (
    <div className={classes.root}>
      {
        !generationStatus ? (
          <div className={classes.header}>
            <CommandImportButton onImport={onGlobalImport} />
            <CloudDownloadOutlinedIcon className={classes.headerIcon} onClick={onGlobalExport} />
            <QueueIcon className={classes.headerIcon} onClick={() => setOpenAddCommandModal(true)} />
            <PowerIcon className={classes.headerIcon} onClick={onGeneration} />
          </div>
        ) : (
          <div className={classes.header}>
            <Typography color="primary" className={classes.loadingText}> Etude en cours de génération...</Typography>
          </div>
        )}
      <div className={classes.body}>
        <CommandListView items={commands} generationStatus={generationStatus} generationIndex={currentCommandGenerationIndex} onDragEnd={onDragEnd} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} onCommandImport={onCommandImport} onCommandExport={onCommandExport} />
      </div>
      {openAddCommandModal && (
        <AddCommandModal
          open={openAddCommandModal}
          onClose={() => setOpenAddCommandModal(false)}
          onNewCommand={onNewCommand}
        />
      )}
    </div>
  );
};

export default connector(EditionView);
