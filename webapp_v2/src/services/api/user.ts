import client from "./client";
import {
  UserDTO,
  GroupDTO,
  RoleCreationDTO,
  UserToken,
  GroupDetailsDTO,
  BotCreateDTO,
  BotDetailsDTO,
  BotDTO,
  RoleDetailsDTO,
  UserDetailsDTO,
} from "../../common/types";

////////////////////////////////////////////////////////////////
// Users
////////////////////////////////////////////////////////////////

interface GetUserParams {
  details: boolean;
}

type UserTypeFromParams<T extends GetUserParams> = T["details"] extends true
  ? UserDetailsDTO
  : UserDTO;

export const getUsers = async <T extends GetUserParams>(
  params?: T
): Promise<Array<UserTypeFromParams<T>>> => {
  const res = await client.get("/v1/users", { params });
  return res.data;
};

export const getUser = async <T extends GetUserParams>(
  id: number,
  params?: T
): Promise<UserTypeFromParams<T>> => {
  const res = await client.get(`/v1/users/${id}`, { params });
  return res.data;
};

export const createUser = async (
  name: string,
  password: string
): Promise<UserDTO> => {
  const data = { name, password };
  const res = await client.post("/v1/users", data);
  return res.data;
};

export const deleteUser = async (id: number): Promise<void> => {
  const res = await client.delete(`/v1/users/${id}`);
  return res.data;
};

////////////////////////////////////////////////////////////////
// Groups
////////////////////////////////////////////////////////////////

interface GetGroupParams {
  details: boolean;
}

type GroupTypeFromParams<T extends GetGroupParams> = T["details"] extends true
  ? GroupDetailsDTO
  : GroupDTO;

export const getGroups = async <T extends GetGroupParams>(
  params?: T
): Promise<Array<GroupTypeFromParams<T>>> => {
  const res = await client.get("/v1/groups", { params });
  return res.data;
};

export const getGroup = async <T extends GetGroupParams>(
  id: string,
  params?: T
): Promise<Array<GroupTypeFromParams<T>>> => {
  const res = await client.get(`/v1/groups/${encodeURIComponent(id)}`, {
    params,
  });
  return res.data;
};

export const createGroup = async (name: string): Promise<GroupDTO> => {
  const data = { name };
  const res = await client.post("/v1/groups", data);
  return res.data;
};

export const updateGroup = async (
  id: string,
  name: string
): Promise<GroupDTO> => {
  const data = { id, name };
  const res = await client.post("/v1/groups", data);
  return res.data;
};

export const deleteGroup = async (id: string): Promise<string> => {
  const res = await client.delete(`/v1/groups/${encodeURIComponent(id)}`);
  return res.data;
};

////////////////////////////////////////////////////////////////
// Roles
////////////////////////////////////////////////////////////////

export const createRole = async (
  role: RoleCreationDTO
): Promise<RoleDetailsDTO> => {
  const data = role;
  const res = await client.post("/v1/roles", data);
  return res.data;
};

export const deleteUserRole = async <
  T extends UserDTO["id"],
  U extends GroupDTO["id"]
>(
  userId: T,
  groupId: U
): Promise<[T, U]> => {
  const res = await client.delete(`/v1/roles/${groupId}/${userId}`);
  return res.data;
};

export const deleteUserRoles = async <T extends UserDTO["id"]>(
  userId: T
): Promise<T> => {
  const res = await client.delete(`/v1/users/roles/${userId}`);
  return res.data;
};

export const getRolesForGroup = async (
  groupId: string
): Promise<RoleDetailsDTO[]> => {
  const res = await client.get(`/v1/roles/group/${groupId}`);
  return res.data;
};

////////////////////////////////////////////////////////////////
// Tokens
////////////////////////////////////////////////////////////////

export const createNewBot = async (bot: BotCreateDTO): Promise<string> => {
  const data = bot;
  const res = await client.post("/v1/bots", data);
  return res.data;
};

export const getBots = async (owner?: number): Promise<Array<BotDTO>> => {
  const req = `/v1/bots${owner ? `?owner=${owner}` : ""}`;
  const res = await client.get(req);
  return res.data;
};

export const getBotInfos = async (id: number): Promise<BotDetailsDTO> => {
  const res = await client.get(`/v1/bots/${id}?verbose=1`);
  return res.data;
};

export const deleteBot = async (id: number): Promise<void> => {
  const res = await client.delete(`/v1/bots/${id}`);
  return res.data;
};

export const getAdminTokenList = async (): Promise<Array<UserToken>> => {
  const users = await getUsers();

  return Promise.all(
    users.map(async (user) => ({
      user,
      bots: await getBots(user.id),
    }))
  );
};
