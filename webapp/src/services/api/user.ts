import client from './client';
import {UserDTO, GroupDTO} from '../../common/types'

export const getUsers = async (): Promise<Array<UserDTO>> => {
  // le client a normalement deja le token (si authentifié)
  const res = await client.get('/users');
  // retour sans try catch mais on pourrait le faire ici si on veut check des codes retours particuliers
  // sinon c'est au composant de faire le try catch et d'afficher un message d'erreur qui va bien
  return res.data;
};

export const getGroups = async (): Promise<Array<GroupDTO>> => {
  const res = await client.get('/groups');
  return res.data;
};


export default {};