import client from './client';
import {UserDTO, UserInfosDTO, GroupDTO, BotRoleUpdateDTO, RoleDTO, BotDTO, TokenDTO} from '../../common/types'


/** ******************************************* */
/* Users                                        */
/** ******************************************* */

export const getUsers = async (): Promise<Array<UserDTO>> => {
  const res = await client.get('/users');
  return res.data;
};


export const getUserInfos = async (id: number) : Promise<UserInfosDTO> => {
  const res = await client.get(`/users/infos/${id}`);
  return res.data;
}

export const createNewUser = async (name: string, password: string) : Promise<any> => {
  const data = { name, password };  
  const res = await client.post('/users', data);
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


export const createRole = async (role : RoleDTO) : Promise<RoleDTO> => {
  const data = {group_id: role.group_id, identity_id: role.user, type : role.type}
  const res = await client.post('/roles', data);
  return res.data;
}

export const updateRole = async (role : RoleDTO) : Promise<any> => {
  const data = {group_id: role.group_id, identity_id: role.user, type : role.type}
  const res = await client.put('/roles', data);
  return res.data;
}

export const deleteRole = async (role : RoleDTO) : Promise<any> => {
  const res = await client.delete(`/roles/${role.group_id}/${role.user}`);
  return res.data;
}

/** ******************************************* */
/* Tokens                                       */
/** ******************************************* */
export const getTokensWithOwner = async (owner: number) : Promise<any> => {
  const res = await client.get(`/bots?owner=${owner}`);
  return res.data;
}

export const getTokens = async () : Promise<any> => {
  const res = await client.get(`/bots`);
  return res.data;
}

export const getBotsInfos = async (id: number) : Promise<UserInfosDTO> => {
  try{
    let res = await client.get(`/bots/infos/${id}`);
    res.data.roles = res.data.roles.map((item : any) => {return {id: item.group_id, name: item.group_name, role: item.type}});
    return res.data;
  }
  catch(e)
  {
    throw e;
  }
}

export const createNewToken = async (bot: BotDTO) : Promise<TokenDTO> => {
  const data = bot;  
  const res = await client.post('/bots', data);
  return res.data;
}

export const updateToken = async (bot: BotRoleUpdateDTO) : Promise<TokenDTO> => {
  const data = bot;
  const res = await client.put('/bots', data);
  return res.data;
}

export const createTokenRoles = async (role: RoleDTO) : Promise<any> => { 
  const data = {group_id: role.group_id, identity_id: role.user, type : role.type} 
  const res = await client.post('/bots/role', data);
  return res.data;
}

export const deleteToken = async (id: number) : Promise<any> => {
  const res = await client.delete(`/bots/${id}`);
  return res.data;
}

export default {};