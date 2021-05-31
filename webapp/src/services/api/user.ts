import client from './client';
import {UserDTO, GroupDTO, RoleDTO, IdentityDTO} from '../../common/types'


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

export const getUserInfos = async (id: number) : Promise<IdentityDTO> => {
  const res = await client.get(`/users/${id}`);
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
  const data = role;
  const res = await client.post('/roles', data);
  return res.data;
}

export const deleteRole = async (role : RoleDTO) : Promise<any> => {
  const res = await client.delete(`/roles/${role.group_id}/${role.identity_id}`);
  return res.data;
}

export const deleteAllRoles = async (id : number) : Promise<any> => {
  const res = await client.delete(`/roles/${id}`);
  return res.data;
}