import { useSnackbar, OptionsObject } from 'notistack';
import { StudyMetadataDTO, StudyMetadata, UserRoleDTO, UserInfo, RoleType} from '../../common/types';

export const convertStudyDtoToMetadata = (sid: string, metadata: StudyMetadataDTO): StudyMetadata => ({
  id: sid,
  name: metadata.caption,
  creationDate: metadata.created,
  modificationDate: metadata.lastsave,
  author: metadata.author,
  version: metadata.version.toString(),
});

export const getStudyIdFromUrl = (url: string): string => {
  const parts = url.trim().split('/');
  return parts[2];
};

export const useNotif = (): (message: React.ReactNode, options?: OptionsObject | undefined) => React.ReactText => {
  const { enqueueSnackbar } = useSnackbar();
  return enqueueSnackbar;
};

export const isUserAdmin = (user : UserInfo) : boolean => {
  if(user)
  {
    const adminElm = user.groups.find((elm : UserRoleDTO) => elm.name === 'admin' && elm.role === RoleType.ADMIN);
    return !!adminElm;
  }
  return false;
}


export default {};
