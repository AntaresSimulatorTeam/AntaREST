import {
  CommandDTO,
  CommandResultDTO,
  TaskDTO,
  TaskStatus,
} from "../../../../common/types";
import { CommandEnum, CommandItem, JsonCommandItem } from "./commandTypes";

export const CommandList = [
  CommandEnum.CREATE_AREA,
  CommandEnum.REMOVE_AREA,
  CommandEnum.CREATE_DISTRICT,
  CommandEnum.REMOVE_DISTRICT,
  CommandEnum.CREATE_LINK,
  CommandEnum.REMOVE_LINK,
  CommandEnum.CREATE_BINDING_CONSTRAINT,
  CommandEnum.UPDATE_BINDING_CONSTRAINT,
  CommandEnum.REMOVE_BINDING_CONSTRAINT,
  CommandEnum.CREATE_CLUSTER,
  CommandEnum.REMOVE_CLUSTER,
  CommandEnum.REPLACE_MATRIX,
  CommandEnum.UPDATE_CONFIG,
];

// a little function to help us with reordering the result
export const reorder = <T>(
  list: T[],
  startIndex: number,
  endIndex: number
): T[] => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);

  return result;
};

export const fromCommandDTOToCommandItem = (
  commands: Array<CommandDTO>
): Array<CommandItem> => {
  const dtoItems: Array<CommandItem> = commands.map((elm) => ({
    id: elm?.id,
    action: elm.action,
    args: elm.args,
    updated: false,
  }));
  return dtoItems;
};

export const fromCommandDTOToJsonCommand = (
  commands: Array<CommandDTO>
): Array<JsonCommandItem> => {
  const dtoItems: Array<JsonCommandItem> = commands.map((elm) => ({
    action: elm.action,
    args: elm.args,
  }));
  return dtoItems;
};

function isString(json: object, name: string): boolean {
  return (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    typeof (json as any)[name] === "string" ||
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (json as any)[name] instanceof String
  );
}

export const checkCommandValidity = (json: object): boolean =>
  "action" in json && "args" in json && isString(json, "action");

export const exportJson = (json: object, filename: string): void => {
  const fileData = JSON.stringify(json);
  const blob = new Blob([fileData], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.download = filename;
  link.href = url;
  link.click();
  link.remove();
};

export const isTaskFinal = (task: TaskDTO): boolean =>
  !(task.status === TaskStatus.PENDING || task.status === TaskStatus.RUNNING);

export const updateCommandResults = (
  studyId: string,
  generationCommands: Array<CommandItem>,
  commandResults: Array<CommandResultDTO>
): { commands: Array<CommandItem>; index: number } => {
  const tmpCommands: Array<CommandItem> = generationCommands.concat([]);
  // eslint-disable-next-line no-plusplus
  for (let i = 0; i < commandResults.length; i++) {
    const commandResult = commandResults[i];
    if (studyId === commandResult.study_id) {
      const index = tmpCommands.findIndex(
        (item) => item.id === commandResult.id
      );
      tmpCommands[index] = { ...tmpCommands[index], results: commandResult };
    }
  }
  let commandGenerationIndex = -1;
  if (tmpCommands.length > 0) {
    // eslint-disable-next-line no-plusplus
    for (let i = tmpCommands.length - 1; i >= 0; i--) {
      const command = tmpCommands[i];
      if (command.results) {
        if (i !== tmpCommands.length - 1) {
          commandGenerationIndex = i + 1;
        }
        break;
      }
    }
  }
  return {
    commands: tmpCommands,
    index: commandGenerationIndex,
  };
};

export default {};
