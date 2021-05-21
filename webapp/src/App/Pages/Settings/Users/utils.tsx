import {RoleDTO, UserRoleDTO, UserDTO } from '../../../../common/types'
import { createNewUser, createRole,deleteRole} from '../../../../services/api/user';

export const prepareDBForRole = async (username : string,
                                       password: string,
                                       initialRoleList : Array<UserRoleDTO>,
                                       onNewUserCreaion : (newUser : UserDTO) => void,
                                       userInfos?: UserDTO) : Promise<number> =>
{
    let tmpUserId = null;
    if(!!userInfos)
    {
        // 1) Call backend (delete all roles)
        tmpUserId = userInfos.id;
        for(const role of initialRoleList)
        {
            const roleData : RoleDTO = {
                group_id: role.id,
                user: userInfos.id,
                type: role.role,
              }

            try{
                let resp = await deleteRole(roleData);
                console.log(resp);
            }
            catch(e)
            {
                console.log(e);
            }
        }
    }
    else
    {
         // 1) Call backend (create new user)
         const newUser = await createNewUser(username,password);
         console.log(newUser)
         tmpUserId = newUser.id;
         onNewUserCreaion(newUser);         
    }

    return tmpUserId;
}

export const createNewRoles = async (userId: number, roleList : Array<UserRoleDTO>) : Promise<any> =>
{
    for(const item of roleList)
    {
        const role : RoleDTO = {
        group_id: item.id,
        user: userId,
        type: item.role};
        const newRole = await createRole(role);
        console.log(newRole);
    }
}

export default {}