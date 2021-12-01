import { RoleType } from '../../../common/types';

interface RoleItem {
    role: RoleType;
    tr: string;
}

export const menuItems: Array<RoleItem> = [
  { role: RoleType.READER, tr: 'settings:readerRole' },
  { role: RoleType.WRITER, tr: 'settings:writerRole' },
  { role: RoleType.RUNNER, tr: 'settings:runnerRole' },
  { role: RoleType.ADMIN, tr: 'settings:adminRole' }];

export default {};
