/* eslint-disable @typescript-eslint/camelcase */
import { RoleCreationDTO, RoleDTO, UserDTO } from '../../../common/types';
import { createNewUser, createRole, deleteAllRoles } from '../../../services/api/user';

export const saveUser = async (
  username: string,
  password: string,
  roleList: Array<RoleDTO>,
  onNewUserCreaion: (newUser: UserDTO) => void,
  userInfos?: UserDTO,
): Promise<number> => {
  let tmpUserId: number;
  if (userInfos) {
    // Delete all user roles
    tmpUserId = userInfos.id;
    await deleteAllRoles(userInfos.id);
  } else {
    // Create new user
    const newUser = await createNewUser(username, password);
    tmpUserId = newUser.id;
    onNewUserCreaion(newUser);
  }

  Promise.all(
    roleList.map(async (item) => {
      const role: RoleCreationDTO = {
        group_id: item.group_id,
        identity_id: tmpUserId,
        type: item.type,
      };
      await createRole(role);
    }),
  );
  return tmpUserId;
};

export default {};
