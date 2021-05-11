import React, {useState, useEffect} from 'react';
import { connect, ConnectedProps } from 'react-redux';
//import debug from 'debug';
import { useTranslation } from 'react-i18next';
//import { useSnackbar } from 'notistack';
//import jwt_decode, {JwtPayload} from 'jwt-decode';
import { AppState } from '../../reducers';
import GenericSettings from '../../../components/Settings/GenericSettings'
import GroupsSettings from './GroupsSettings';
import TokensSettings from './TokensSettings';
import UsersSettings from './UsersSettings';


// pour connecter à redux les 3 choses suivantes et wrapper le composant à l'export (derniere ligne)
const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const connector = connect(mapState);

// Quand le composant et wrappé le type des props est défini comme ceci
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps;

const UserSettings = (props: PropTypes) => {

  const { user} = props;
  console.log(user);

  const [isAdmin, setAdminStatus] = useState<boolean>(false);
  
  const [t] = useTranslation();
  // lib https://iamhosseindhv.com/notistack qui permet d'afficher simplement des notifs material ui
  //const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {

    // Ici on détermine si l'utilisateur est admin ou pas
    setAdminStatus(true);
  
  }, [user])

  const adminUserData = {
    [t('settings:users')]: () => <UsersSettings />,
    [t('settings:groups')]: () => <GroupsSettings />,
    [t('settings:tokens')]: () => <TokensSettings />,
  }

  const normalUserData = {
    [t('settings:users')]: () => <UsersSettings />,
  }

  /*  Ici il s'agit de données d'exemples. Backend pas prêt ?  */
  const myUser = {

    username: "bernard54", 
    firstname: "Bernard", 
    lastname: "Jacob"
  }

  return (<GenericSettings items={isAdmin ? adminUserData : normalUserData} userInfos={myUser} />)
};

export default connector(UserSettings);