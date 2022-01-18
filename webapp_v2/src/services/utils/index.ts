import moment from 'moment';
import { useSnackbar, OptionsObject } from 'notistack';
import { StudyMetadataDTO, StudyMetadata, JWTGroup, UserInfo, RoleType, VariantTreeDTO, VariantTree, GenericInfo } from '../../common/types';

export const convertStudyDtoToMetadata = (sid: string, metadata: StudyMetadataDTO): StudyMetadata => ({
  id: sid,
  name: metadata.name,
  creationDate: metadata.created,
  modificationDate: metadata.updated,
  owner: metadata.owner,
  groups: metadata.groups,
  type: metadata.type,
  publicMode: metadata.public_mode,
  version: metadata.version.toString(),
  workspace: metadata.workspace,
  managed: metadata.managed,
  archived: metadata.archived,
  folder: metadata.folder,
});

export const convertVariantTreeDTO = (variantTree: VariantTreeDTO): VariantTree => ({
  node: convertStudyDtoToMetadata(variantTree.node.id, variantTree.node),
  children: (variantTree.children || []).map((child: VariantTreeDTO) => convertVariantTreeDTO(child)),
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

export const isGroupAdmin = (user: UserInfo): boolean => {
  if (user) {
    const adminElm = user.groups.find((elm: JWTGroup) => elm.role === RoleType.ADMIN);
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

export const hasAuthorization = (user: UserInfo | undefined, study: StudyMetadata, role: RoleType): boolean => {
  if (user) {
    // User is super admin
    if (isUserAdmin(user)) {
      return true;
    }

    if (study) {
      // User is owner of this study
      if (study.owner.id && study.owner.id === user.id) {
        return true;
      }
      // User is admin of 1 of study groups
      return (
        study.groups.findIndex((studyGroupElm) =>
          user.groups.find(
            (userGroupElm) =>
              studyGroupElm.id === userGroupElm.id && userGroupElm.role >= role,
          )) >= 0
      );
    }
  }
  return false;
};

export const getStudyExtendedName = (study: StudyMetadata): string => {
  if (study.folder) {
    return `${study.name} (${study.folder})`;
  }
  return study.name;
};

export const convertUTCToLocalTime = (date: string): string => moment.utc(date).local().format('YYYY-MM-DD HH:mm:ss');

export const exportText = (fileData: string, filename: string): void => {
  const blob = new Blob([fileData], { type: 'application/txt' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.download = filename;
  link.href = url;
  link.click();
  link.remove();
};

export const displayVersionName = (version: string): string => version.split('').join('.');

export const convertVersions = (versions: Array<string>): Array<GenericInfo> => versions.map((version) => (
  {
    id: version,
    name: displayVersionName(version),
  }));

export default {};
