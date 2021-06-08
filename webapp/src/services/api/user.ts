import client from './client';
import {UserDTO,
        GroupDTO,
        RoleCreationDTO,
        RoleDTO,
        UserToken,
        UserGroup,
        IdentityDTO,
        BotCreateDTO,
        BotIdentityDTO,
        BotDTO
      } from '../../common/types'


/** ******************************************* */
/* Users                                        */
/** ******************************************* */

export const getUsers = async (): Promise<Array<UserDTO>> => {
  const res = await client.get('/users');
  return res.data;
};

export const createNewUser = async (name: string, password: string) : Promise<any> => {
  const data = { name, password };  
  const res = await client.post('/users', data);
  return res.data;
}

export const getUser = async (id: number) : Promise<UserDTO> => {
  const res = await client.get(`/users/${id}`);
  return res.data;
}

export const getUserInfos = async (id: number) : Promise<IdentityDTO> => {
  const res = await client.get(`/users/${id}?details=true`);
  return res.data;
}

export const deleteUser = async (id: number) : Promise<any> => {
  const res = await client.delete(`/users/${id}`);
  return res.data;
}


/** ******************************************* */
/* Groups                                       */
/** ******************************************* */

export const getGroups = async (): Promise<Array<GroupDTO>> => {
  const res = await client.get('/groups');
  return res.data;
};

export const getGroupInfos = async (id: string) : Promise<UserGroup> =>{
  const res = await client.get(`/groups/${id}?details=true`);
  return res.data;
}

export const createGroup = async (name: string): Promise<GroupDTO> => {
  const data = { name };  
  const res = await client.post('/groups', data);
  return res.data;
};

export const updateGroup = async (id: string, name: string): Promise<GroupDTO> => {
  const data = { id, name };  
  const res = await client.post('/groups', data);
  return res.data;
};

export const deleteGroup = async (id: string): Promise<string> => { 
  const res = await client.delete(`/groups/${id}`);
  return res.data;
};


/** ******************************************* */
/* Roles                                        */
/** ******************************************* */

export const getAllRolesInGroup = async (group_id : string) : Promise<Array<RoleDTO>> => {
  const res = await client.get(`/roles/group/${group_id}`);
  return res.data;
}

export const createRole = async (role : RoleCreationDTO) : Promise<any> => {
  const data = role;
  const res = await client.post('/roles', data);
  return res.data;
}

export const deleteAllRoles = async (id : number) : Promise<any> => {
  const res = await client.delete(`/users/roles/${id}`);
  return res.data;
}

/** ******************************************* */
/* Tokens                                       */
/** ******************************************* */

export const createNewBot = async (bot: BotCreateDTO) : Promise<any> => {
  const data = bot;  
  const res = await client.post('/bots', data);
  return res.data;
}

export const getBots = async (owner?: number) : Promise<Array<BotDTO>> => {
  let req = '/bots'+(!!owner ? `?owner=${owner}`:'');
  const res = await client.get(req);
  return res.data;
}

export const getBotInfos = async (id: number) : Promise<BotIdentityDTO> =>{
  const res = await client.get(`/bots/${id}?verbose=1`);
  return res.data;
}


export const deleteBot = async (id: number) : Promise<any> => {
  const res = await client.delete(`/bots/${id}`);
  return res.data;
}

export const getAdminTokenList = async () : Promise<Array<UserToken>> => {
  try{

    const tokenList : Array<UserToken> = [];
    const users = await getUsers();

    for(const user of users)
      tokenList.push({ user, bots: await getBots(user.id)})
    return tokenList;
  }
  catch(e)
  {
    throw e;
  }
}