import {BotCreateDTO, RoleDTO, BotDTO } from '../../../../../common/types'
import { createNewBot} from '../../../../../services/api/user';
import jwt_decode from 'jwt-decode';

export const saveToken = async (name : string,
                               isAuthor: boolean,
                               roleList : Array<RoleDTO>,
                               onNewTokenCreaion : (newToken : string, newBot: BotDTO) => void) : Promise<any> =>
{
    try{
            let newBot : BotCreateDTO = {
                name,
                is_author: isAuthor,
                roles: []
            }
            for(const role of roleList)
            {
                newBot.roles.push({group: role.group_id,
                                   role: role.type})
            }

            const newToken : string = await createNewBot(newBot);
            const tokenData = jwt_decode(newToken); 
            const subject = JSON.parse((tokenData as any).sub);

            let createdBot : BotDTO = {
                id: subject.id,
                name,
                owner: -1,
                isAuthor
            }
            onNewTokenCreaion(newToken, createdBot);
    }
    catch(e)
    {
        throw e;
    }
}

export default {}