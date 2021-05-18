import { useSnackbar, OptionsObject } from 'notistack';
import jwt_decode from 'jwt-decode';
import { StudyMetadataDTO, StudyMetadata, UserGroupInfo} from '../../common/types';

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

export const isUserAdmin = (access_token : string) : boolean => {
    const token = jwt_decode(access_token);
    console.log('YOOOO')
    console.log(token)
    const adminElm = (token as any).sub.groups.find((elm : UserGroupInfo) => elm.name === 'admin' && elm.role === 40);
    return !!adminElm;
}


export default {};
