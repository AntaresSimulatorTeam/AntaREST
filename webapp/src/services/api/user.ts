import client from './client';
import {UserDTO, GroupDTO, RoleDTO} from '../../common/types'


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
  const data = {group_id: role.group_id, identity_id: role.user_id, type : role.type}
  const res = await client.post('/roles', data);
  return res.data;
}

export const deleteRole = async (role : RoleDTO) : Promise<any> => {
  const res = await client.delete(`/roles/${role.group_id}/${role.user_id}`);
  return res.data;
}