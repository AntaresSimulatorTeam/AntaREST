import { CommandDTO } from '../../../common/types';
import { appendCommand, moveCommand, updateCommand, deleteCommand } from '../../../services/api/variant';
import { CommandItem } from './CommandTypes';

// a little function to help us with reordering the result
export const reorder = <T>(
  list: T[],
  startIndex: number,
  endIndex: number,
): T[] => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);

  return result;
};

export const fromCommandDTOToCommandItem = (commands: Array<CommandDTO>): Array<CommandItem> => {
  const dtoItems: Array<CommandItem> = commands.map((elm) => {
    const dtoItem: CommandItem = { id: elm?.id, name: elm.id !== undefined ? elm.id : '', action: elm.action, args: elm.args };
    return dtoItem;
  });
  return dtoItems;
};

export const fromCommandItemToCommandDTO = (commands: Array<CommandItem>): Array<CommandDTO> => {
  const dtoItems: Array<CommandDTO> = commands.map((elm) => {
    const dtoItem: CommandDTO = { id: elm?.id, action: elm.action, args: elm.args };
    return dtoItem;
  });
  return dtoItems;
};

export const onCommandsSave = async (studyId: string, initCommand: Array<CommandItem>, newCommandList: Array<CommandItem>): Promise<Array<CommandItem>> => {
  let commandList = fromCommandItemToCommandDTO(newCommandList);
  let dbCommandRepr = fromCommandItemToCommandDTO(initCommand);

  // 1) Remove deleted commands
  dbCommandRepr = await Promise.all(dbCommandRepr.map(async (elm) => {
    const index = commandList.findIndex((item) => item.id === elm.id);
    if (index < 0) {
      await deleteCommand(studyId, (elm.id as string));
    }
    return elm;
  }));

  dbCommandRepr = dbCommandRepr.filter((elm) => commandList.findIndex((item) => item.id === elm.id) >= 0);

  // 2) Append all new commands
  commandList = await Promise.all(commandList.map(async (elm) => {
    if (elm.id === undefined) {
      const newId = await appendCommand(studyId, elm);
      const newElmt: CommandDTO = { ...elm, id: newId };
      dbCommandRepr.push(newElmt);
      return newElmt;
    }
    return elm;
  }));

  // 3) Move commands
  await Promise.all(commandList.map(async (elm, index) => {
    const initIndex = dbCommandRepr.findIndex((dbElm) => dbElm.id === elm.id);
    const item = dbCommandRepr[initIndex];
    // Update if needed
    if (item.args !== elm.args) {
      await updateCommand(studyId, (elm.id as string), elm);
    }
    // Move to index
    if (initIndex !== index) {
      await moveCommand(studyId, (item.id as string), index);
    }
  }));

  return fromCommandDTOToCommandItem(commandList);
};

export default {};
