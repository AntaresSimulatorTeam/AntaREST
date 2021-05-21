import React, {useState, useEffect} from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../../../components/Settings/GenericModal';
import GroupsAssignmentView from '../../../../components/Settings/GroupsAssignmentView';
import { getGroups, getUserInfos} from '../../../../services/api/user';
import {GroupDTO, RoleType, UserRoleDTO, UserDTO } from '../../../../common/types';
import {prepareDBForRole, createNewRoles} from './utils';


const useStyles = makeStyles((theme: Theme) => createStyles({
    infos: {
      flex: '1',
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
      padding: theme.spacing(2),
    },
    idFields: {
        width: '70%',
        height: '30px',
        boxSizing: 'border-box',
        margin: theme.spacing(2)
    }
  }));

interface PropTypes {
    open: boolean;
    userInfos?: UserDTO;
    onNewUserCreaion : (newUser : UserDTO) => void;
    onClose: () => void;
};

const UserModal = (props: PropTypes) => {

    const classes = useStyles();
    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const {open, userInfos, onNewUserCreaion, onClose} = props;
    const [groupList, setGroupList] = useState<GroupDTO[]>([]); 
    const [roleList, setRoleList] = useState<UserRoleDTO[]>([]);
    const [initialRoleList, setInitialRoleList] = useState<UserRoleDTO[]>([]);
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');   
    const [selectedGroup, setActiveGroup] = useState<GroupDTO>({id: '', name:''});

    const onChange = (group: GroupDTO) => {
        setActiveGroup(group);
    }

    const addRoleToList = () => {
        //1) Look if role is already added to list
        if(roleList.find((item) => item.id === selectedGroup.id))
            return ;
        //2) Create a new role with type == READER
        const newRole : UserRoleDTO = {
            id: selectedGroup.id,
            name: selectedGroup.name,
            role: RoleType.READER // READER by default
        }
        //3) Add the role in roleList
        setRoleList(roleList.concat([newRole]));
    }

    const deleteRoleFromList = (group_id: string) => {
        // Delete role from roleList
        const tmpList = roleList.filter((item) => item.id !== group_id);
        setRoleList(tmpList);
    }

    // Update Role in roleList
    const updateRoleFromList = (group_id: string, role : RoleType) => {
        // 1) Find the role
        const tmpList : UserRoleDTO[] = ([] as UserRoleDTO[]).concat(roleList);
        const index = roleList.findIndex((item) => item.id === group_id);
        if(index >= 0)
        {
            // 2) Update role in roleList
            tmpList[index].role = role;
            setRoleList(tmpList);
        }
    }

    const onSave = async () => {
        try{
            // 1) Create new user or delete previous role list in DB
            let tmpUserId = await prepareDBForRole(username,password,initialRoleList,onNewUserCreaion,userInfos);
            // 2) Create roles
            await createNewRoles(tmpUserId, roleList);
            setInitialRoleList(roleList);

            if(!!userInfos)
                enqueueSnackbar(t('settings:onUserUpdate'), { variant: 'success' });
            else
            enqueueSnackbar(t('settings:onUserCreation'), { variant: 'success' });
        }
        catch(e)
        {
            enqueueSnackbar(t('settings:onUserSaveError'), { variant: 'error' });
        }
    }

    useEffect(() => {
        const init = async () =>{
            try {
              // 1) Get list of all groups and add it to groupList or locally from access_token
              const groups = await getGroups();
              const filteredGroup = groups.filter((item) => item.id !== "admin");
              setGroupList(filteredGroup);

              if(filteredGroup.length > 0)
                setActiveGroup(filteredGroup[0]);

                // 2) If userInfos exist => get list of user roles and update roleList
                if(!!userInfos)
                {
                    const users =  await getUserInfos(userInfos.id);
                    const filteredRoles = users.roles.filter((item) => item.id !== "admin")
                    console.log(filteredRoles)
                    setRoleList(filteredRoles);
                    setInitialRoleList(filteredRoles);
                }
            }
            catch (e)
            {
              enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
            }
          }
          init();
    }, [userInfos, t, enqueueSnackbar])

    return (
        <GenericModal 
        open={open}
        handleClose={onClose}
        handleSave={onSave}
        title={userInfos ? userInfos.name : t('settings:newUserTitle')}>
            {
                !userInfos &&
                (<div className={classes.infos}>
                    <TextField className={classes.idFields}
                               value={username}
                               onChange={(event) => setUsername(event.target.value as string)}
                               label={t('settings:usernameLabel')}
                               variant="outlined" />
                    <TextField className={classes.idFields}
                            label={t('settings:passwordLabel')}
                            value={password}
                            onChange={(event) => setPassword(event.target.value as string)}
                            type="password"
                            variant="outlined"/>
                </div>)

            }

            <GroupsAssignmentView groupsList={groupList}
                                roleList={roleList}
                                selectedGroup={selectedGroup}
                                onChange={onChange}
                                addRole={addRoleToList}
                                deleteRole={deleteRoleFromList}
                                updateRole={updateRoleFromList} />
      </GenericModal>       
    )

}

export default UserModal;


