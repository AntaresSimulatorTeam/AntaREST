import { CommandDTO } from '../../../common/types';
import { CommandEnum, CommandItem, JsonCommandItem } from './CommandTypes';

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
  const dtoItems: Array<CommandItem> = commands.map((elm) => ({ id: elm?.id, action: elm.action, args: elm.args, updated: false }));
  return dtoItems;
};

export const fromCommandDTOToJsonCommand = (commands: Array<CommandDTO>): Array<JsonCommandItem> => {
  const dtoItems: Array<JsonCommandItem> = commands.map((elm) => ({ action: elm.action, args: elm.args }));
  return dtoItems;
};

function isString(json: object, name: string): boolean {
  return (typeof (json as any)[name] === 'string' || (json as any)[name] instanceof String);
}

export const checkCommandValidity = (json: object): boolean => ('action' in json && 'args' in json && isString(json, 'action'));

export const exportJson = (json: object, filename: string): void => {
  const fileData = JSON.stringify(json);
  const blob = new Blob([fileData], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.download = filename;
  link.href = url;
  link.click();
  link.remove();
};

export default {};
