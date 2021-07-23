/* eslint-disable @typescript-eslint/camelcase */
// eslint-disable-next-line camelcase
import jwt_decode from 'jwt-decode';
import { BotCreateDTO, RoleDTO, BotDTO } from '../../../../common/types';
import { createNewBot } from '../../../../services/api/user';

export const saveToken = async (
  name: string,
  isAuthor: boolean,
  roleList: Array<RoleDTO>,
  onNewTokenCreaion: (newToken: string, newBot: BotDTO) => void,
): Promise<any> => {
  const newBot: BotCreateDTO = {
    name,
    is_author: isAuthor,
    roles: roleList.map((role) => ({ group: role.group_id, role: role.type })),
  };

  const newToken: string = await createNewBot(newBot);
  const tokenData = jwt_decode(newToken);
  const subject = JSON.parse((tokenData as any).sub);

  const createdBot: BotDTO = {
    id: subject.id,
    name,
    owner: -1,
    isAuthor,
  };
  onNewTokenCreaion(newToken, createdBot);
};

export default {};
