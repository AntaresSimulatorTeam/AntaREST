import { GroupDTO, StudyMetadataOwner, StudyPublicMode, UserDTO } from '../../common/types';
import { changeStudyOwner, addStudyGroup, deleteStudyGroup, changePublicMode } from '../../services/api/study';

export const updatePermission = async (
  studyId: string,
  initGroups: Array<GroupDTO>,
  initPublicMode: StudyPublicMode,
  owner: StudyMetadataOwner,
  newOwner: UserDTO | undefined,
  newGroups: Array<GroupDTO>,
  newPublicMode: StudyPublicMode,
  updateInfos: (newOwner: StudyMetadataOwner, newGroups: Array<GroupDTO>, newPublicMode: StudyPublicMode,) => void,
): Promise<any> => {
  if (newOwner) {
    await changeStudyOwner(studyId, newOwner.id);
  }

  if (initPublicMode !== newPublicMode) {
    await changePublicMode(studyId, newPublicMode);
  }

  await Promise.all(initGroups.map(async (elm) => {
    if (newGroups.findIndex((item) => item.id === elm.id) < 0) {
      await deleteStudyGroup(studyId, elm.id);
    }
  }));

  await Promise.all(newGroups.map(async (elm) => {
    if (initGroups.findIndex((item) => item.id === elm.id) < 0) {
      await addStudyGroup(studyId, elm.id);
    }
  }));

  updateInfos(newOwner ? newOwner as StudyMetadataOwner : owner, newGroups, newPublicMode);
};

export default {};
