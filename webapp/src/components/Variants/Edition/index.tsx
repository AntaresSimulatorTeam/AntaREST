import React, { useCallback, useEffect, useState } from 'react';
import { makeStyles, createStyles, Theme, Typography, Button } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { DropResult } from 'react-beautiful-dnd';
import QueueIcon from '@material-ui/icons/Queue';
import CloudDownloadOutlinedIcon from '@material-ui/icons/CloudDownloadOutlined';
import { connect, ConnectedProps } from 'react-redux';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import debug from 'debug';
import { CommandItem, JsonCommandItem } from './CommandTypes';
import CommandListView from './DraggableCommands/CommandListView';
import { reorder, fromCommandDTOToCommandItem, fromCommandDTOToJsonCommand, exportJson, isTaskFinal } from './utils';
import { appendCommand, deleteCommand, getCommand, getCommands, moveCommand, updateCommand, replaceCommands, applyCommands, getTask } from '../../../services/api/variant';
import AddCommandModal from './AddCommandModal';
import { CommandDTO, WSEvent, WSMessage, CommandResultDTO, TaskLogDTO, TaskEventPayload } from '../../../common/types';
import CommandImportButton from './DraggableCommands/CommandImportButton';
import { addListener, removeListener } from '../../../ducks/websockets';

const logInfo = debug('antares:variantedition:info');

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
    width: '90%',
    height: '80px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  editHeader: {
    flex: 1,
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
  backButton: {
    width: 'auto',
    height: 'auto',
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 3),
    '&:hover': {
      color: theme.palette.secondary.main,
      borderColor: theme.palette.secondary.main,
    },
  },
  loadingText: {
    backgroundColor: theme.palette.action.selected,
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    borderRadius: theme.shape.borderRadius,
    margin: theme.spacing(0, 3),
  },
  switchContainer: {
    width: 'auto',
    height: '70px',
    padding: `${theme.spacing(1)} 0px`,
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: '0px',
    margin: theme.spacing(0, 3),
  },
  editModeTitle: {
    fontWeight: 'bold',
    color: theme.palette.primary.main,
    borderBottom: `4px solid ${theme.palette.primary.main}`,
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
  const [currentCommandGenerationIndex, setCurrentCommandGenerationIndex] = useState<number>(-1);
  const [expandedIndex, setExpandedIndex] = useState<number>(-1);
  const [commands, setCommands] = useState<Array<CommandItem>>([]);

  const onDragEnd = async ({ destination, source }: DropResult) => {
    // dropped outside the list
    if (!destination) return;
    const oldCommands = commands.concat([]);
    try {
      const elm = commands[source.index];
      const newItems = reorder(commands, source.index, destination.index);
      setCommands(newItems.map((item) => ({ ...item, results: undefined })));
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
      setCommands((commandList) => commandList.filter((item, idx) => idx !== index).map((item) => ({ ...item, results: undefined })));
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
      await applyCommands(studyId);
      setGenerationStatus(true);
      enqueueSnackbar(t('variants:launchGenerationSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(t('variants:launchGenerationError'), { variant: 'error' });
    }
  };

  const onExpanded = (index: number, value: boolean) => {
    if (value) {
      setExpandedIndex(index);
    } else {
      setExpandedIndex(-1);
    }
  };

  const listen = useCallback((ev: WSMessage) => {
    const manageCommandResults = (commandResult: CommandResultDTO) => {
      if (studyId === commandResult.study_id) {
        let tmpCommand: Array<CommandItem> = [];
        tmpCommand = tmpCommand.concat(commands);
        const index = tmpCommand.findIndex((item) => item.id === commandResult.id);
        tmpCommand[index] = { ...tmpCommand[index], results: commandResult };
        if (currentCommandGenerationIndex === commands.length - 1) {
          setCurrentCommandGenerationIndex(-1);
        } else {
          setCurrentCommandGenerationIndex(currentCommandGenerationIndex + 1);
        }
        setCommands(tmpCommand);
      }
    };

    const taskStart = (taskPayload: TaskEventPayload) => {
      if (taskPayload.message === studyId) {
        if (commands.length > 0) setCurrentCommandGenerationIndex(0);
        setGenerationStatus(true);
      }
    };

    const taskEnd = (taskPayload: TaskEventPayload, event: WSEvent) => {
      if (taskPayload.message === studyId) {
        setCurrentCommandGenerationIndex(-1);
        if (event === WSEvent.TASK_COMPLETED) enqueueSnackbar(t('variants:taskCompleted'), { variant: 'success' });
        else enqueueSnackbar(t('variants:taskFailed'), { variant: 'error' });
        setGenerationStatus(false);
      }
    };

    switch (ev.type) {
      case WSEvent.STUDY_VARIANT_GENERATION_COMMAND_RESULT:
        manageCommandResults(ev.payload as CommandResultDTO);
        break;
      case WSEvent.TASK_STARTED:
        console.log('EVENT STARTED: ', ev);
        taskStart(ev.payload as TaskEventPayload);
        break;
      case WSEvent.TASK_COMPLETED:
      case WSEvent.TASK_FAILED:
        console.log('EVENT FINISH: ', ev);
        taskEnd(ev.payload as TaskEventPayload, ev.type);
        break;
      default:
        break;
    }
  }, [commands, currentCommandGenerationIndex, enqueueSnackbar, studyId, t]);

  useEffect(() => {
    const init = async () => {
      let items: Array<CommandItem> = [];
      try {
        const dtoItems = await getCommands(studyId);
        items = fromCommandDTOToCommandItem(dtoItems);
      } catch (e) {
        console.log(e);
        enqueueSnackbar(t('variants:fetchCommandError'), { variant: 'error' });
      }

      try {
        const task = await getTask(studyId);

        let currentIndex = -1;
        const isFinal = isTaskFinal(task);

        if (task.logs === undefined || task.logs.length === 0) {
          if (!isFinal) { currentIndex = 0; }
        } else {
          task.logs.forEach((elm: TaskLogDTO, i: number) => {
            const results: CommandResultDTO = (JSON.parse(elm.message) as CommandResultDTO);
            if (i < items.length && items[i].id === results.id) items[i] = { ...items[i], results };
          });
          if (!isFinal) {
            currentIndex = (commands.length > task.logs.length) ? task.logs.length : -1;
          }
        }
        setCurrentCommandGenerationIndex(currentIndex);
        setGenerationStatus(!isFinal);
        setCommands(items);
      } catch (error) {
        console.log(error);
      }
      setCommands(items);
    };
    init();
  }, [commands.length, enqueueSnackbar, studyId, t]);

  useEffect(() => {
    addWsListener(listen);
    return () => removeWsListener(listen);
  }, [addWsListener, listen, removeWsListener]);

  return (
    <div className={classes.root}>
      {
        !generationStatus ? (
          <div className={classes.header}>
            <Button color="primary" variant="outlined" onClick={onGeneration}>
              <FontAwesomeIcon icon="bolt" style={{ marginRight: '0.6em' }} />
              <Typography>Generate</Typography>
            </Button>
            <div className={classes.editHeader}>
              <CommandImportButton onImport={onGlobalImport} />
              <CloudDownloadOutlinedIcon className={classes.headerIcon} onClick={onGlobalExport} />
              <QueueIcon className={classes.headerIcon} onClick={() => setOpenAddCommandModal(true)} />
            </div>
          </div>
        ) : (
          <div className={classes.header}>
            <Typography color="primary" className={classes.loadingText}>{t('variants:generationInProgress')}</Typography>
          </div>
        )}
      <div className={classes.body}>
        <CommandListView items={commands} generationStatus={generationStatus} expandedIndex={expandedIndex} generationIndex={currentCommandGenerationIndex} onDragEnd={onDragEnd} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} onCommandImport={onCommandImport} onCommandExport={onCommandExport} onExpanded={onExpanded} />
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
