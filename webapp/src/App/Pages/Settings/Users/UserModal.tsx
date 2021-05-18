import React, {useState, useEffect} from 'react';
import { createStyles, makeStyles, Theme, TextField } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../../../components/Settings/GenericModal';
import GroupsAssignmentView from '../../../../components/Settings/GroupsAssignmentView';
import { getGroups} from '../../../../services/api/user';
import {GroupDTO, RoleType, RoleDTO, UserDTO } from '../../../../common/types'


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
    user: {
        newUser: boolean;
        userInfos: UserDTO|undefined;
    };
    onClose: () => void;
};

const UserModal = (props: PropTypes) => {

    const classes = useStyles();
    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const {open, user, onClose} = props;
    const [groupList, setGroupList] = useState<GroupDTO[]>([]); // Which type ?
    const [roleList, setRoleList] = useState<RoleDTO[]>([]); // Which type ? 
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');   
    const [selectedGroupId, setActiveGroup] = useState<string>(''); // Current selected group

    const onChange = (group_id: string) => {
        
        setActiveGroup(group_id);

        // Est-ce que l'on connaît déjà tous les groupes 
        console.log('Change '+group_id)
    }

    const addRole = (groupId: string) => {

        //1) Look if role already add to list
        if(roleList.find((item) => item.group_id === groupId))
            return ;

        //2) Create a new role with empty type
        const newRole : RoleDTO = {
            group_id: groupId,
            user: user && user.newUser && user.userInfos ? user.userInfos.id : -1,
            type: 10
        }
        setRoleList(roleList.concat([newRole]));
        //3) Add the role in roleList
        console.log('Add role') 
    }

    const deleteRole = (group_id: string) => {

        // Delete group from roleList
        const tmpList = roleList.filter((item) => item.group_id !== group_id);
        setRoleList(tmpList);
        console.log('Delete '+group_id)
    }

    const updateRoleType = (group_id : string, type: RoleType) => {
        
        // 1) Find the role
        const tmpList : RoleDTO[] = ([] as RoleDTO[]).concat(roleList);
        const index = roleList.findIndex((item) => item.group_id === group_id);
        if(index >= 0)
        {
            tmpList[index].type = type;
            setRoleList(tmpList);
        }

        // 2) Update the type 
        console.log('Set Group Role (id: '+group_id+', newType : '+type+')')
    }

    const onSave = () => {
        if(user.newUser)
        {
            // 1) Call backend (create user)
            // 2) call enqueueSnackbar with green success message
        }
        else
        {
             // 1) Call backend (update user roles)
            // 2) call enqueueSnackbar with green success message           
        }
    }

    useEffect(() => {
        const init = async () =>{

            try {
              // 1) Get list of all groups and it to groupList
              const groups = await getGroups();
              setGroupList(groups);

              if(groups.length > 0)
                setActiveGroup(groups[0].id);
      
                // 2) If !user.newUser => get list of user roles and update roleList

            } catch (e) {
              enqueueSnackbar(t('settings:groupsError'), { variant: 'error' });
            }
      
          }
          init();
    }, [t, enqueueSnackbar])

    return (

        <GenericModal 
        open={open}
        handleClose={onClose}
        handleSave={onSave}
        title={user.newUser ? 'Create new user' : (user.userInfos ? user.userInfos.name : '')}>
            {
                user.newUser &&
                (<div className={classes.infos}>
                    <TextField className={classes.idFields}
                               value={username}
                               onChange={(event) => setUsername(event.target.value as string)}
                               label="Username"
                               variant="outlined" />
                    <TextField className={classes.idFields}
                            label="Password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value as string)}
                            type="password"
                            variant="outlined"/>
                </div>)

            }
          <GroupsAssignmentView groupsList={groupList}
                                roleList={roleList}
                                selectedGroupId={selectedGroupId}
                                onChange={onChange}
                                addRole={addRole}
                                deleteRole={deleteRole}
                                updateRoleType={updateRoleType} />
      </GenericModal>       
    )

}

export default UserModal;


