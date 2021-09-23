import { CommandDTO } from '../../../common/types';
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
    const dtoItem: CommandItem = { name: elm.id !== undefined ? elm.id : '', action: elm.action, args: elm.args };
    return dtoItem;
  });
  return dtoItems;
};

export const fromCommandItemToCommandDTO = (commands: Array<CommandItem>): Array<CommandDTO> => {
  const dtoItems: Array<CommandDTO> = commands.map((elm) => {
    const dtoItem: CommandDTO = { action: elm.action, args: elm.args };
    return dtoItem;
  });
  return dtoItems;
};

export default {};