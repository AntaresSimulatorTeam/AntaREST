import React, { useCallback, useEffect, useRef, useState } from 'react';
import { makeStyles, createStyles, Theme, Typography, Button } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import { DropResult } from 'react-beautiful-dnd';
import _ from 'lodash';
import QueueIcon from '@material-ui/icons/Queue';
import CloudDownloadOutlinedIcon from '@material-ui/icons/CloudDownloadOutlined';
import { connect, ConnectedProps } from 'react-redux';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import debug from 'debug';
import { AxiosError } from 'axios';
import HelpIcon from '@material-ui/icons/Help';
import { CommandItem, JsonCommandItem } from './CommandTypes';
import CommandListView from './DraggableCommands/CommandListView';
import { reorder, fromCommandDTOToCommandItem, fromCommandDTOToJsonCommand, exportJson, isTaskFinal, updateCommandResults } from './utils';
import { appendCommand, deleteCommand, getCommand, getCommands, moveCommand, updateCommand, replaceCommands, applyCommands, getTask, getStudyTask } from '../../../services/api/variant';
import AddCommandModal from './AddCommandModal';
import { CommandDTO, WSEvent, WSMessage, CommandResultDTO, TaskEventPayload, TaskStatus } from '../../../common/types';
import CommandImportButton from './DraggableCommands/CommandImportButton';
import { addListener, removeListener, subscribe, unsubscribe, WsChannel } from '../../../ducks/websockets';
import enqueueErrorSnackbar from '../../ui/ErrorSnackBar';
import NoContent from '../../ui/NoContent';
import SimpleLoader from '../../ui/loaders/SimpleLoader';

const logError = debug('antares:variantedition:error');

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
    position: 'relative',
  },
  bodyNoContent: {
    width: '100%',
    maxHeight: '90%',
    minHeight: '90%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'left',
    overflow: 'auto',
    boxSizing: 'border-box',
    position: 'relative',
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
  newCommand: {
    border: `2px solid ${theme.palette.primary.main}`,
    '&:hover': {
      border: `2px solid ${theme.palette.secondary.main}`,
      color: theme.palette.secondary.main,
    },
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
  subscribeChannel: subscribe,
  unsubscribeChannel: unsubscribe,
});

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnTypes;

const EditionView = (props: PropTypes) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { studyId, addWsListener, removeWsListener, subscribeChannel, unsubscribeChannel } = props;
  const [openAddCommandModal, setOpenAddCommandModal] = useState<boolean>(false);
  const [generationStatus, setGenerationStatus] = useState<boolean>(false);
  const [generationTaskId, setGenerationTaskId] = useState<string>();
  const [currentCommandGenerationIndex, setCurrentCommandGenerationIndex] = useState<number>(-1);
  const [expandedIndex, setExpandedIndex] = useState<number>(-1);
  const [commands, setCommands] = useState<Array<CommandItem>>([]);
  const [loaded, setLoaded] = useState(false);
  const taskFetchPeriod = 3000;
  const taskTimeoutId = useRef<NodeJS.Timeout>();

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
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:moveError'), e as AxiosError);
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
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:saveError'), e as AxiosError);
    }
  };

  const onDelete = async (index: number) => {
    try {
      const elm = commands[index];
      await deleteCommand(studyId, (elm.id as string));
      setCommands((commandList) => commandList.filter((item, idx) => idx !== index).map((item) => ({ ...item, results: undefined })));
      enqueueSnackbar(t('variants:deleteSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:deleteError'), e as AxiosError);
    }
  };

  const onNewCommand = async (action: string) => {
    try {
      const elmDTO: CommandDTO = { action, args: {} };
      const newId = await appendCommand(studyId, elmDTO);
      setCommands(commands.concat([{ ...elmDTO, id: newId, updated: false }]));
      enqueueSnackbar(t('variants:addSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:addError'), e as AxiosError);
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
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:importError'), e as AxiosError);
    }
  };

  const onCommandExport = async (index: number) => {
    try {
      const elm = await getCommand(studyId, commands[index].id as string);
      exportJson({ action: elm.action, args: elm.args }, `${elm.id}_command.json`);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:exportError'), e as AxiosError);
    }
  };

  const onGlobalExport = async () => {
    try {
      const items = await getCommands(studyId);
      exportJson(fromCommandDTOToJsonCommand(items), `${studyId}_commands.json`);
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:exportError'), e as AxiosError);
    }
  };

  const onGlobalImport = async (json: object) => {
    setLoaded(false);
    try {
      const globalJson: Array<JsonCommandItem> = (json as Array<JsonCommandItem>);
      await replaceCommands(studyId, globalJson);

      const dtoItems = await getCommands(studyId);
      setCommands(fromCommandDTOToCommandItem(dtoItems));
      enqueueSnackbar(t('variants:importSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:importError'), e as AxiosError);
    } finally {
      setLoaded(true);
    }
  };

  const onGeneration = async () => {
    try {
      // Get commands
      const dtoItems = await getCommands(studyId);
      setCommands(fromCommandDTOToCommandItem(dtoItems));
      setCurrentCommandGenerationIndex(0);
      // Launch generation task
      const res = await applyCommands(studyId);
      setGenerationTaskId(res);
      setGenerationStatus(true);
      enqueueSnackbar(t('variants:launchGenerationSuccess'), { variant: 'success' });
    } catch (e) {
      enqueueErrorSnackbar(enqueueSnackbar, t('variants:launchGenerationError'), e as AxiosError);
    }
  };

  const onExpanded = (index: number, value: boolean) => {
    if (value) {
      setExpandedIndex(index);
    } else {
      setExpandedIndex(-1);
    }
  };

  const doUpdateCommandResults = useCallback((commandResults: Array<CommandResultDTO>) => {
    const res = updateCommandResults(studyId, commands, commandResults);
    setCurrentCommandGenerationIndex(res.index);
    setCommands(res.commands);
  }, [studyId, commands]);

  const listen = useCallback((ev: WSMessage) => {
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
        setGenerationTaskId(undefined);
      }
    };

    switch (ev.type) {
      case WSEvent.STUDY_VARIANT_GENERATION_COMMAND_RESULT:
        doUpdateCommandResults([ev.payload as CommandResultDTO]);
        break;
      case WSEvent.TASK_ADDED:
        taskStart(ev.payload as TaskEventPayload);
        break;
      case WSEvent.TASK_COMPLETED:
      case WSEvent.TASK_FAILED:
        taskEnd(ev.payload as TaskEventPayload, ev.type);
        break;
      default:
        break;
    }
  }, [commands.length, doUpdateCommandResults, enqueueSnackbar, studyId, t]);

  const fetchTask = useCallback(async () => {
    if (generationStatus && generationTaskId) {
      const tmpTask = await getTask(generationTaskId);
      if (isTaskFinal(tmpTask)) {
        setGenerationStatus(false);
        setGenerationTaskId(undefined);
      }
    }
  }, [generationStatus, generationTaskId]);

  const debouncedFailureNotification = useCallback(_.debounce(() => {
    enqueueSnackbar(t('variants:taskFailed'), { variant: 'error' });
  }, 1000, { trailing: false, leading: true }), [enqueueSnackbar, t]);

  useEffect(() => {
    const commandGenerationChannel = WsChannel.STUDY_GENERATION + studyId;
    subscribeChannel(commandGenerationChannel);
    const init = async () => {
      let items: Array<CommandItem> = [];
      setLoaded(false);
      try {
        const dtoItems = await getCommands(studyId);
        items = fromCommandDTOToCommandItem(dtoItems);
      } catch (e) {
        logError('Error: ', e);
        enqueueErrorSnackbar(enqueueSnackbar, t('variants:fetchCommandError'), e as AxiosError);
      }

      try {
        const task = await getStudyTask(studyId);

        let currentIndex = -1;
        const isFinal = isTaskFinal(task);

        if (task.logs === undefined || task.logs.length === 0) {
          if (!isFinal) { currentIndex = 0; } else if (task.status !== TaskStatus.COMPLETED) {
            debouncedFailureNotification();
          }
        } else {
          const res = updateCommandResults(studyId, items, task.logs.map((elm) => (JSON.parse(elm.message) as CommandResultDTO)));
          items = res.commands;
          currentIndex = res.index;
        }
        if (!isFinal) {
          setGenerationTaskId(task.id);
        }
        setCurrentCommandGenerationIndex(currentIndex);
        setGenerationStatus(!isFinal);
        setCommands(items);
      } catch (error) {
        logError('Error: ', error);
      }
      setCommands(items);
      setLoaded(true);
    };
    init();
    return () => unsubscribeChannel(commandGenerationChannel);
  }, [commands.length, enqueueSnackbar, studyId, t, subscribeChannel, unsubscribeChannel, debouncedFailureNotification]);

  useEffect(() => {
    addWsListener(listen);
    return () => removeWsListener(listen);
  }, [addWsListener, listen, removeWsListener]);

  useEffect(() => {
    if (generationTaskId) {
      const taskChannel = WsChannel.TASK + generationTaskId;
      subscribeChannel(taskChannel);
      if (taskTimeoutId.current) {
        clearTimeout(taskTimeoutId.current);
      }
      taskTimeoutId.current = setTimeout(fetchTask, taskFetchPeriod);
      return () => unsubscribeChannel(taskChannel);
    }
    return () => { if (taskTimeoutId.current) { clearTimeout(taskTimeoutId.current); } };
  }, [fetchTask, generationTaskId, subscribeChannel, unsubscribeChannel]);

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
              <a
                href="https://antares-web.readthedocs.io/en/latest/user-guide/2-variant_manager/"
                target="_blank"
                rel="noopener noreferrer"
              >
                <HelpIcon className={classes.headerIcon} />
              </a>
            </div>
          </div>
        ) : (
          <div className={classes.header}>
            <Typography color="primary" className={classes.loadingText}>{t('variants:generationInProgress')}</Typography>
          </div>
        )}
      {loaded && commands.length > 0 ? (
        <div className={classes.body}>
          <CommandListView items={commands} generationStatus={generationStatus} expandedIndex={expandedIndex} generationIndex={currentCommandGenerationIndex} onDragEnd={onDragEnd} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} onCommandImport={onCommandImport} onCommandExport={onCommandExport} onExpanded={onExpanded} />
        </div>
      ) : loaded && (
        <div className={classes.bodyNoContent}>
          <div style={{ height: '85%' }}>
            <NoContent
              title="variants:noCommands"
              callToAction={<Button className={classes.newCommand} color="primary" variant="outlined" onClick={() => setOpenAddCommandModal(true)}>{t('variants:newCommandButton')}</Button>}
            />
          </div>
        </div>
      )}
      {!loaded && (
      <div className={classes.body}>
        <SimpleLoader color="" />
      </div>
      )}
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
