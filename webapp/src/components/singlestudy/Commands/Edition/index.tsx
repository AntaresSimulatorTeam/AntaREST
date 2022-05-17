import { useCallback, useEffect, useRef, useState } from "react";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { DropResult } from "react-beautiful-dnd";
import _ from "lodash";
import QueueIcon from "@mui/icons-material/Queue";
import CloudDownloadOutlinedIcon from "@mui/icons-material/CloudDownloadOutlined";
import BoltIcon from "@mui/icons-material/Bolt";
import debug from "debug";
import { AxiosError } from "axios";
import HelpIcon from "@mui/icons-material/Help";
import { Box, Button, Typography } from "@mui/material";
import { CommandItem, JsonCommandItem } from "./commandTypes";
import CommandListView from "./DraggableCommands/CommandListView";
import {
  reorder,
  fromCommandDTOToCommandItem,
  fromCommandDTOToJsonCommand,
  exportJson,
  isTaskFinal,
  updateCommandResults,
} from "./utils";
import {
  appendCommand,
  deleteCommand,
  getCommand,
  getCommands,
  moveCommand,
  updateCommand,
  replaceCommands,
  applyCommands,
  getStudyTask,
} from "../../../../services/api/variant";
import AddCommandDialog from "./AddCommandDialog";
import {
  CommandDTO,
  WSEvent,
  WSMessage,
  CommandResultDTO,
  TaskEventPayload,
  TaskStatus,
} from "../../../../common/types";
import CommandImportButton from "./DraggableCommands/CommandImportButton";
import { getTask } from "../../../../services/api/tasks";
import { Body, EditHeader, Header, headerIconStyle, Root } from "./style";
import SimpleLoader from "../../../common/loaders/SimpleLoader";
import NoContent from "../../../common/page/NoContent";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import {
  addMessageListener,
  sendSubscribeMessage,
  WsChannel,
} from "../../../../services/webSockets";

const logError = debug("antares:variantedition:error");

interface Props {
  studyId: string;
}

function EditionView(props: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { studyId } = props;
  const [openAddCommandDialog, setOpenAddCommandDialog] =
    useState<boolean>(false);
  const [generationStatus, setGenerationStatus] = useState<boolean>(false);
  const [generationTaskId, setGenerationTaskId] = useState<string>();
  const [currentCommandGenerationIndex, setCurrentCommandGenerationIndex] =
    useState<number>(-1);
  const [expandedIndex, setExpandedIndex] = useState<number>(-1);
  const [commands, setCommands] = useState<Array<CommandItem>>([]);
  const [loaded, setLoaded] = useState(false);
  const taskFetchPeriod = 3000;
  // eslint-disable-next-line no-undef
  const taskTimeoutId = useRef<NodeJS.Timeout>();

  const onDragEnd = async ({ destination, source }: DropResult) => {
    // dropped outside the list
    if (!destination) return;
    const oldCommands = commands.concat([]);
    try {
      const elm = commands[source.index];
      const newItems = reorder(commands, source.index, destination.index);
      setCommands(newItems.map((item) => ({ ...item, results: undefined })));
      await moveCommand(studyId, elm.id as string, destination.index);
      enqueueSnackbar(t("variants:moveSuccess"), { variant: "success" });
    } catch (e) {
      setCommands(oldCommands);
      enqueueErrorSnackbar(t("variants:moveError"), e as AxiosError);
    }
  };

  const onSave = async (index: number) => {
    try {
      const elm = commands[index];
      if (elm.updated) {
        await updateCommand(studyId, elm.id as string, elm);
        let tmpCommand: Array<CommandItem> = [];
        tmpCommand = tmpCommand.concat(commands);
        tmpCommand[index].updated = false;
        setCommands(tmpCommand);
        enqueueSnackbar(t("variants:saveSuccess"), { variant: "success" });
      }
    } catch (e) {
      enqueueErrorSnackbar(t("variants:saveError"), e as AxiosError);
    }
  };

  const onDelete = async (index: number) => {
    try {
      const elm = commands[index];
      await deleteCommand(studyId, elm.id as string);
      setCommands((commandList) =>
        commandList
          .filter((item, idx) => idx !== index)
          .map((item) => ({ ...item, results: undefined }))
      );
      enqueueSnackbar(t("variants:deleteSuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("variants:deleteError"), e as AxiosError);
    }
  };

  const onNewCommand = async (action: string) => {
    try {
      const elmDTO: CommandDTO = { action, args: {} };
      const newId = await appendCommand(studyId, elmDTO);
      setCommands(commands.concat([{ ...elmDTO, id: newId, updated: false }]));
      enqueueSnackbar(t("variants:addSuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("variants:addError"), e as AxiosError);
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
      await updateCommand(studyId, elm.id as string, elm);
      setCommands(tmpCommand);
      enqueueSnackbar(t("variants:importSuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("variants:importError"), e as AxiosError);
    }
  };

  const onCommandExport = async (index: number) => {
    try {
      const elm = await getCommand(studyId, commands[index].id as string);
      exportJson(
        { action: elm.action, args: elm.args },
        `${elm.id}_command.json`
      );
    } catch (e) {
      enqueueErrorSnackbar(t("variants:exportError"), e as AxiosError);
    }
  };

  const onGlobalExport = async () => {
    try {
      const items = await getCommands(studyId);
      exportJson(
        fromCommandDTOToJsonCommand(items),
        `${studyId}_commands.json`
      );
    } catch (e) {
      enqueueErrorSnackbar(t("variants:exportError"), e as AxiosError);
    }
  };

  const onGlobalImport = async (json: object) => {
    setLoaded(false);
    try {
      const globalJson: Array<JsonCommandItem> = json as Array<JsonCommandItem>;
      await replaceCommands(studyId, globalJson);

      const dtoItems = await getCommands(studyId);
      setCommands(fromCommandDTOToCommandItem(dtoItems));
      enqueueSnackbar(t("variants:importSuccess"), { variant: "success" });
    } catch (e) {
      enqueueErrorSnackbar(t("variants:importError"), e as AxiosError);
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
      enqueueSnackbar(t("variants:launchGenerationSuccess"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(
        t("variants:launchGenerationError"),
        e as AxiosError
      );
    }
  };

  const onExpanded = (index: number, value: boolean) => {
    if (value) {
      setExpandedIndex(index);
    } else {
      setExpandedIndex(-1);
    }
  };

  const doUpdateCommandResults = useCallback(
    (commandResults: Array<CommandResultDTO>) => {
      const res = updateCommandResults(studyId, commands, commandResults);
      setCurrentCommandGenerationIndex(res.index);
      setCommands(res.commands);
    },
    [studyId, commands]
  );

  const listen = useCallback(
    (ev: WSMessage) => {
      const taskStart = (taskPayload: TaskEventPayload) => {
        if (taskPayload.message === studyId) {
          if (commands.length > 0) setCurrentCommandGenerationIndex(0);
          setGenerationStatus(true);
        }
      };

      const taskEnd = (taskPayload: TaskEventPayload, event: WSEvent) => {
        if (taskPayload.message === studyId) {
          setCurrentCommandGenerationIndex(-1);
          if (event === WSEvent.TASK_COMPLETED)
            enqueueSnackbar(t("variants:taskCompleted"), {
              variant: "success",
            });
          else enqueueSnackbar(t("variants:taskFailed"), { variant: "error" });
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
    },
    [commands.length, doUpdateCommandResults, enqueueSnackbar, studyId, t]
  );

  const fetchTask = useCallback(async () => {
    if (generationStatus && generationTaskId) {
      const tmpTask = await getTask(generationTaskId);
      if (isTaskFinal(tmpTask)) {
        setGenerationStatus(false);
        setGenerationTaskId(undefined);
      }
    }
  }, [generationStatus, generationTaskId]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedFailureNotification = useCallback(
    _.debounce(
      () => {
        enqueueSnackbar(t("variants:taskFailed"), { variant: "error" });
      },
      1000,
      { trailing: false, leading: true }
    ),
    [enqueueSnackbar, t]
  );

  useEffect(() => {
    const commandGenerationChannel = WsChannel.StudyGeneration + studyId;
    const unsubscribe = sendSubscribeMessage(commandGenerationChannel);

    const init = async () => {
      let items: Array<CommandItem> = [];
      setLoaded(false);
      try {
        const dtoItems = await getCommands(studyId);
        items = fromCommandDTOToCommandItem(dtoItems);
      } catch (e) {
        logError("Error: ", e);
        enqueueErrorSnackbar(t("variants:fetchCommandError"), e as AxiosError);
      }

      try {
        const task = await getStudyTask(studyId);

        let currentIndex = -1;
        const isFinal = isTaskFinal(task);

        if (task.logs === undefined || task.logs.length === 0) {
          if (!isFinal) {
            currentIndex = 0;
          } else if (task.status !== TaskStatus.COMPLETED) {
            debouncedFailureNotification();
          }
        } else {
          const res = updateCommandResults(
            studyId,
            items,
            task.logs.map((elm) => JSON.parse(elm.message) as CommandResultDTO)
          );
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
        logError("Error: ", error);
      }
      setCommands(items);
      setLoaded(true);
    };
    init();

    return () => unsubscribe();
  }, [
    commands.length,
    enqueueSnackbar,
    enqueueErrorSnackbar,
    studyId,
    t,
    debouncedFailureNotification,
  ]);

  useEffect(() => {
    return addMessageListener(listen);
  }, [listen]);

  useEffect(() => {
    if (generationTaskId) {
      // TODO Maybe WsChannel.StudyGeneration?
      const taskChannel = WsChannel.Task + generationTaskId;
      const unsubscribe = sendSubscribeMessage(taskChannel);

      if (taskTimeoutId.current) {
        clearTimeout(taskTimeoutId.current);
      }
      taskTimeoutId.current = setTimeout(fetchTask, taskFetchPeriod);

      return () => unsubscribe();
    }
    return () => {
      if (taskTimeoutId.current) {
        clearTimeout(taskTimeoutId.current);
      }
    };
  }, [fetchTask, generationTaskId]);

  return (
    <Root>
      {!generationStatus ? (
        <Header>
          <Button color="primary" variant="outlined" onClick={onGeneration}>
            <BoltIcon sx={{ mr: 1 }} />
            <Typography>Generate</Typography>
          </Button>
          <EditHeader>
            <CommandImportButton onImport={onGlobalImport} />
            <CloudDownloadOutlinedIcon
              sx={{ ...headerIconStyle }}
              onClick={onGlobalExport}
            />
            <QueueIcon
              sx={{ ...headerIconStyle }}
              onClick={() => setOpenAddCommandDialog(true)}
            />
            <a
              href="https://antares-web.readthedocs.io/en/latest/user-guide/2-variant_manager/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <HelpIcon sx={{ ...headerIconStyle }} />
            </a>
          </EditHeader>
        </Header>
      ) : (
        <Header>
          <Typography
            color="primary"
            sx={{
              bgcolor: "action.selected",
              px: 1,
              borderRadius: "shape.borderRadius",
              mx: 3,
            }}
          >
            {t("variants:generationInProgress")}
          </Typography>
        </Header>
      )}
      {loaded && commands.length > 0 ? (
        <Body>
          <CommandListView
            items={commands}
            generationStatus={generationStatus}
            expandedIndex={expandedIndex}
            generationIndex={currentCommandGenerationIndex}
            onDragEnd={onDragEnd}
            onDelete={onDelete}
            onArgsUpdate={onArgsUpdate}
            onSave={onSave}
            onCommandImport={onCommandImport}
            onCommandExport={onCommandExport}
            onExpanded={onExpanded}
          />
        </Body>
      ) : (
        loaded && (
          <Body sx={{ alignItems: "left" }}>
            <Box height="85%">
              <NoContent
                title="variants:noCommands"
                callToAction={
                  <Button
                    color="primary"
                    variant="outlined"
                    onClick={() => setOpenAddCommandDialog(true)}
                  >
                    {t("variants:newCommandButton")}
                  </Button>
                }
              />
            </Box>
          </Body>
        )
      )}
      {!loaded && (
        <Body>
          <SimpleLoader color="" />
        </Body>
      )}
      {openAddCommandDialog && (
        <AddCommandDialog
          open={openAddCommandDialog}
          onClose={() => setOpenAddCommandDialog(false)}
          onNewCommand={onNewCommand}
        />
      )}
    </Root>
  );
}

export default EditionView;
