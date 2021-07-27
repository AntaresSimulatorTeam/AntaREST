import { useSnackbar, OptionsObject } from 'notistack';
import { StudyMetadataDTO, StudyMetadata, JWTGroup, UserInfo, RoleType } from '../../common/types';

export const convertStudyDtoToMetadata = (sid: string, metadata: StudyMetadataDTO): StudyMetadata => ({
  id: sid,
  name: metadata.name,
  creationDate: metadata.created,
  modificationDate: metadata.updated,
  owner: metadata.owner,
  groups: metadata.groups,
  publicMode: metadata.public_mode,
  version: metadata.version.toString(),
  workspace: metadata.workspace,
  managed: metadata.managed,
});

export const useNotif = (): (message: React.ReactNode, options?: OptionsObject | undefined) => React.ReactText => {
  const { enqueueSnackbar } = useSnackbar();
  return enqueueSnackbar;
};

export const isUserAdmin = (user: UserInfo): boolean => {
  if (user) {
    const adminElm = user.groups.find((elm: JWTGroup) => elm.id === 'admin' && elm.role === RoleType.ADMIN);
    return !!adminElm;
  }
  return false;
};

export const roleToString = (role: RoleType): string => {
  switch (role) {
    case RoleType.ADMIN:
      return 'settings:adminRole';

    case RoleType.RUNNER:
      return 'settings:runnerRole';

    case RoleType.WRITER:
      return 'settings:writerRole';

    case RoleType.READER:
      return 'settings:readerRole';

    default:
      break;
  }
  return '';
};

export default {};
