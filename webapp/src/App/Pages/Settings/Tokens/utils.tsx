import {BotDTO, TokenDTO, BotRoleUpdateDTO, RoleDTO, UserRoleDTO } from '../../../../common/types'
import { createNewToken,createTokenRoles, updateToken, deleteRole} from '../../../../services/api/user';

export const prepareDBForRole = async (tokenName : string,
                                       isAuthor: boolean,
                                       initialRoleList : Array<UserRoleDTO>,
                                       onNewTokenCreation : (newToken : TokenDTO) => void,
                                       onUpdateToken : (id: number, name : string, isAuthor: boolean) => void,
                                       tokenInfos?: TokenDTO) : Promise<number> =>
{
    let tmpTokenId = null;
    // 1) If it's not a new token
    if(!!tokenInfos)
    {
        tmpTokenId = tokenInfos.id;
        // 1) Change token name or isAuthor flag if needed
        if(tokenInfos.name !== tokenName || tokenInfos.isAuthor !== isAuthor)
        {
            try{
                const role : BotRoleUpdateDTO = {
                    id: tokenInfos.id,
                    name: tokenName,
                    is_author: isAuthor
                }
                console.log('isAuthor '+isAuthor)
                const resp = await updateToken(role);
                console.log(resp);
            }
            catch(e)
            {
                console.log(e);
                throw e;
            }
        }

        // 2) Delete all existing roles for this token
        for(const role of initialRoleList)
        {
            const roleData : RoleDTO = {
                group_id: role.id,
                user: tokenInfos.id,
                type: role.role,
              }
            try{
                let resp = await deleteRole(roleData);
                console.log(resp);
            }
            catch(e)
            {
                console.log(e);
                throw e;
            }
        }
        onUpdateToken(tmpTokenId,tokenName,isAuthor);
    }
    else // New token
    {
         const bot : BotDTO = {
             name: tokenName,
             is_author: isAuthor
         }
        try {
            // Create a new token (calling backend)
            const newToken = await createNewToken(bot);
            console.log(newToken)
            tmpTokenId = newToken.id;
            onNewTokenCreation(newToken); 
        }
        catch(e)
        {
            console.log(e);
            throw e;
        }      
    }
    return tmpTokenId;
}


export const createNewRoles = async (tokenId: number, roleList : Array<UserRoleDTO>) : Promise<any> =>
{
    // Create a new roles for token
    for(const item of roleList)
    {
        const role : RoleDTO = {
        group_id: item.id,
        user: tokenId,
        type: item.role};
        
        const newRole = await createTokenRoles(role);
        console.log(newRole);
    }
}

export default {}