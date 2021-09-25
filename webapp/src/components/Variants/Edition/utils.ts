import { CommandDTO } from '../../../common/types';
import { CommandEnum, CommandItem } from './CommandTypes';

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
  endIndex: number,
): T[] => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);

  return result;
};

export const fromCommandDTOToCommandItem = (commands: Array<CommandDTO>): Array<CommandItem> => {
  const dtoItems: Array<CommandItem> = commands.map((elm) => {
    const dtoItem: CommandItem = { id: elm?.id, action: elm.action, args: elm.args, updated: false };
    return dtoItem;
  });
  return dtoItems;
};

export default {};
