import { GroupDTO, StudyPublicMode } from '../../common/types';
import { changeStudyOwner, addStudyGroup, deleteStudyGroup, changePublicMode } from '../../services/api/study';
import { getUser } from '../../services/api/user';

export const updatePermission = async (
  studyId: string,
  initOwnerId: number,
  initOwnerName: string,
  initGroups: Array<GroupDTO>,
  initPublicMode: StudyPublicMode,
  newOwnerId: number,
  newGroups: Array<GroupDTO>,
  newPublicMode: StudyPublicMode,
  updateInfos: (newOwnerId: number, newOwnerName: string, newGroups: Array<GroupDTO>, newPublicMode: StudyPublicMode,) => void,
): Promise<any> => {
  let newOwnerName = initOwnerName;

  if (initOwnerId !== newOwnerId) {
    await changeStudyOwner(studyId, newOwnerId);
    const res = await getUser(newOwnerId);
    newOwnerName = res.name;
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

  updateInfos(newOwnerId, newOwnerName, newGroups, newPublicMode);
};

export default {};
