import client from './client';
import {
  UserDTO,
  GroupDTO,
  RoleCreationDTO,
  RoleDTO,
  UserToken,
  UserGroup,
  IdentityDTO,
  BotCreateDTO,
  BotIdentityDTO,
  BotDTO,
} from '../../common/types';

/** ******************************************* */
/* Users                                        */
/** ******************************************* */

export const getUsers = async (): Promise<Array<UserDTO>> => {
  const res = await client.get('/v1/users');
  return res.data;
};

export const createNewUser = async (name: string, password: string): Promise<any> => {
  const data = { name, password };
  const res = await client.post('/v1/users', data);
  return res.data;
};

export const getUser = async (id: number): Promise<IdentityDTO> => {
  const res = await client.get(`/v1/users/${id}`);
  return res.data;
};

export const getUserInfos = async (id: number): Promise<IdentityDTO> => {
  const res = await client.get(`/v1/users/${id}?details=true`);
  return res.data;
};

export const deleteUser = async (id: number): Promise<any> => {
  const res = await client.delete(`/v1/users/${id}`);
  return res.data;
};

/** ******************************************* */
/* Groups                                       */
/** ******************************************* */

export const getGroups = async (): Promise<Array<GroupDTO>> => {
  const res = await client.get('/v1/groups');
  return res.data;
};

export const getGroupInfos = async (id: string): Promise<UserGroup> => {
  const res = await client.get(`/v1/groups/${id}?details=true`);
  return res.data;
};

export const createGroup = async (name: string): Promise<GroupDTO> => {
  const data = { name };
  const res = await client.post('/v1/groups', data);
  return res.data;
};

export const updateGroup = async (id: string, name: string): Promise<GroupDTO> => {
  const data = { id, name };
  const res = await client.post('/v1/groups', data);
  return res.data;
};

export const deleteGroup = async (id: string): Promise<string> => {
  const res = await client.delete(`/v1/groups/${id}`);
  return res.data;
};

/** ******************************************* */
/* Roles                                        */
/** ******************************************* */

export const getAllRolesInGroup = async (groupId: string): Promise<Array<RoleDTO>> => {
  const res = await client.get(`/v1/roles/group/${groupId}`);
  return res.data;
};

export const createRole = async (role: RoleCreationDTO): Promise<any> => {
  const data = role;
  const res = await client.post('/v1/roles', data);
  return res.data;
};

export const deleteAllRoles = async (id: number): Promise<any> => {
  const res = await client.delete(`/v1/users/roles/${id}`);
  return res.data;
};

/** ******************************************* */
/* Tokens                                       */
/** ******************************************* */

export const createNewBot = async (bot: BotCreateDTO): Promise<any> => {
  const data = bot;
  const res = await client.post('/v1/bots', data);
  return res.data;
};

export const getBots = async (owner?: number): Promise<Array<BotDTO>> => {
  const req = `/v1/bots${owner ? `?owner=${owner}` : ''}`;
  const res = await client.get(req);
  return res.data;
};

export const getBotInfos = async (id: number): Promise<BotIdentityDTO> => {
  const res = await client.get(`/v1/bots/${id}?verbose=1`);
  return res.data;
};

export const deleteBot = async (id: number): Promise<any> => {
  const res = await client.delete(`/v1/bots/${id}`);
  return res.data;
};

export const getAdminTokenList = async (): Promise<Array<UserToken>> => {
  const users = await getUsers();

  return Promise.all(
    users.map(async (user) => ({
      user,
      bots: await getBots(user.id),
    })),
  );
};
