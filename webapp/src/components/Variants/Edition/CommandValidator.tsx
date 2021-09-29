/* eslint-disable dot-notation */
import { type } from 'os';
import { CommandEnum } from './CommandTypes';

export interface CommandValidityResult {
    result: boolean;
    message: string;
}

function exist(json: object, name: string): CommandValidityResult {
  const result: CommandValidityResult = { result: false, message: '' };
  if (!(name in json)) {
    result.message = `"${name}" not found`;
    return result;
  }
  result.result = true;
  return result;
}

function isString(json: object, name: string): CommandValidityResult {
  const result: CommandValidityResult = { result: false, message: '' };
  if (!(typeof (json as any)[name] === 'string' || (json as any)[name] instanceof String)) {
    result.message = `"${name}" is not a string`;
    return result;
  }
  result.result = true;
  return result;
}

function isNumber(json: object, name: string): CommandValidityResult {
  const result: CommandValidityResult = { result: false, message: '' };
  if (!(typeof (json as any)[name] === 'number' || (json as any)[name] instanceof Number)) {
    result.message = `"${name}" is not a number`;
    return result;
  }
  result.result = true;
  return result;
}

function isObject(json: object, name: string): CommandValidityResult {
  const result: CommandValidityResult = { result: false, message: '' };
  if (!(typeof (json as any)[name] === 'object' || (json as any)[name] instanceof Object)) {
    result.message = `"${name}" is not a object`;
    return result;
  }
  result.result = true;
  return result;
}

function isBoolean(json: object, name: string): CommandValidityResult {
  const result: CommandValidityResult = { result: false, message: '' };
  if (!(typeof (json as any)[name] === 'boolean' || (json as any)[name] instanceof Boolean)) {
    result.message = `"${name}" is not a boolean`;
    return result;
  }
  result.result = true;
  return result;
}

enum TypeType {
    STRING = 'string',
    BOOLEAN = 'boolean',
    NUMBER = 'number',
    OBJECT = 'object',
}

function existanceAndType(json: object, name: string, types: Array<TypeType>): CommandValidityResult {
  let result: CommandValidityResult = { result: false, message: '' };
  result = exist(json, name);
  if (!result.result) return result;

  result.result = false;

  for (let i = 0; i < types.length; i += 1) {
    switch (types[i]) {
      case TypeType.STRING:
        result = isString(json, name);
        break;

      case TypeType.BOOLEAN:
        result = isBoolean(json, name);
        break;

      case TypeType.NUMBER:
        result = isNumber(json, name);
        break;

      default:
        result = isObject(json, name);
        break;
    }
    if (result.result) break;
  }

  if (!result.result) {
    result.message = `${name} has wrong type`;
  }

  return result;
}

function existanceAndStringType(json: object, name: string): CommandValidityResult {
  return existanceAndType(json, name, [TypeType.STRING]);
}

function existanceAndBooleanType(json: object, name: string): CommandValidityResult {
  return existanceAndType(json, name, [TypeType.BOOLEAN]);
}

function existanceAndNumberType(json: object, name: string): CommandValidityResult {
  return existanceAndType(json, name, [TypeType.NUMBER]);
}

function existanceAndObjectType(json: object, name: string): CommandValidityResult {
  return existanceAndType(json, name, [TypeType.OBJECT]);
}

function checkCreateArea(json: object): CommandValidityResult {
  let result: CommandValidityResult = { result: false, message: '' };
  result = existanceAndStringType(json, 'area_name');
  if (!result.result) return result;

  result.result = true;
  return result;
}

function checkCreateBindingConstraint(json: object): CommandValidityResult {
  let result: CommandValidityResult = { result: false, message: '' };
  result = existanceAndStringType(json, 'name');
  if (!result.result) return result;

  result = existanceAndBooleanType(json, 'enabled');
  if (!result.result) return result;

  result = existanceAndStringType(json, 'time_step');
  if (!result.result) return result;

  result = existanceAndStringType(json, 'operator');
  if (!result.result) return result;

  result = existanceAndObjectType(json, 'coeffs');
  if (!result.result) return result;

  result.result = true;
  return result;
}

export function checkCommandValidity(json: object): CommandValidityResult {
  let result: CommandValidityResult = { result: true, message: '' };
  result = existanceAndStringType(json, 'action');
  if (!result.result) return result;

  result = existanceAndObjectType(json, 'args');
  if (!result.result) return result;

  /*
  switch (json['action']) {
    case CommandEnum.CREATE_AREA:
      return checkCreateArea(json['args']);
    case CommandEnum.REMOVE_AREA:
      return checkCreateArea(json['args']);
    case CommandEnum.CREATE_DISTRICT:
      return checkCreateArea(json['args']);
    case CommandEnum.REMOVE_DISTRICT:
      return checkCreateArea(json['args']);
    case CommandEnum.CREATE_LINK:
      return checkCreateArea(json['args']);
    case CommandEnum.REMOVE_LINK:
      return checkCreateArea(json['args']);
    case CommandEnum.CREATE_BINDING_CONSTRAINT:
      return checkCreateArea(json['args']);
    case CommandEnum.UPDATE_BINDING_CONSTRAINT:
      return checkCreateArea(json['args']);
    case CommandEnum.REMOVE_BINDING_CONSTRAINT:
      return checkCreateArea(json['args']);
    case CommandEnum.CREATE_CLUSTER:
      return checkCreateArea(json['args']);
    case CommandEnum.REMOVE_CLUSTER:
      return checkCreateArea(json['args']);
    case CommandEnum.REPLACE_MATRIX:
      return checkCreateArea(json['args']);
    case CommandEnum.UPDATE_CONFIG:
      return checkCreateArea(json['args']);
    default:
      result.result = false;
      result.message = 'This Json command is not valid. Unknown command !';
      return result;
  }*/
  return result;
}

export default {};
