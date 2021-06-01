import {RoleCreationDTO, RoleDTO, UserDTO } from '../../../../common/types'
import { createNewUser, createRole, deleteAllRoles} from '../../../../services/api/user';

export const saveUser = async (username : string,
                               password: string,
                               roleList : Array<RoleDTO>,
                               onNewUserCreaion : (newUser : UserDTO) => void,
                               userInfos?: UserDTO) : Promise<number> =>
{
    let tmpUserId = null;
    try{
        if(!!userInfos)
        {
            // Delete all user roles
            tmpUserId = userInfos.id;
            await deleteAllRoles(userInfos.id);
        }
        else
        {
            // Create new user
            const newUser = await createNewUser(username,password);
            tmpUserId = newUser.id;
            onNewUserCreaion(newUser); 
        }

        for(const item of roleList)
        {
            const role : RoleCreationDTO = {
            group_id: item.group_id,
            identity_id: tmpUserId,
            type: item.type};
            await createRole(role);
        }
    }
    catch(e)
    {
        throw e;
    }
    return tmpUserId;
}

export default {}