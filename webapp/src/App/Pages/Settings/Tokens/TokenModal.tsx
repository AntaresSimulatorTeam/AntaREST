import React, {useState, useEffect} from 'react';
import { createStyles, makeStyles, Theme, TextField, Typography } from '@material-ui/core';
import { useSnackbar } from 'notistack';
import { useTranslation } from 'react-i18next';
import GenericModal from '../../../../components/Settings/GenericModal';
import GroupsAssignmentView from '../../../../components/Settings/GroupsAssignmentView';
import Checkbox from '@material-ui/core/Checkbox';
import {getGroups, getBotsInfos} from '../../../../services/api/user';
import {GroupDTO, RoleType, UserRoleDTO, TokenDTO } from '../../../../common/types';
import {prepareDBForRole, createNewRoles} from './utils';


const useStyles = makeStyles((theme: Theme) => createStyles({
    infos: {
      flex: '1',
      width: '100%',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
      padding: theme.spacing(2),
    },
    idFields: {
        width: '50%',
        height: '30px',
        boxSizing: 'border-box',
        margin: theme.spacing(2)
    },
    checkbox: {
        display: 'flex',
        flexFlow: 'row nowrap',
        justifyContent: 'flex-start',
        alignItems: 'center',
        margin: theme.spacing(2)
    }
  }));
  

interface PropTypes {
    open: boolean;
    tokenInfos?: TokenDTO;
    onNewTokenCreation : (newToken : TokenDTO) => void;
    onUpdateToken : (id: number, name : string, isAuthor: boolean) => void;
    onClose: () => void;
};

const TokenModal = (props: PropTypes) => {

    const classes = useStyles();
    const [t] = useTranslation();
    const { enqueueSnackbar } = useSnackbar();
    const {open, tokenInfos, onNewTokenCreation, onUpdateToken, onClose} = props;
    const [groupList, setGroupList] = useState<Array<GroupDTO>>([]); 
    const [roleList, setRoleList] = useState<Array<UserRoleDTO>>([]);
    const [initialRoleList, setInitialRoleList] = useState<Array<UserRoleDTO>>([]);
    const [tokenName, setTokenName] = useState<string>('');
    const [checked, setChecked] = useState<boolean>(false);
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
            let tmpTokenId = await prepareDBForRole(tokenName,
                                                    checked,
                                                    initialRoleList,
                                                    onNewTokenCreation,
                                                    onUpdateToken,
                                                    tokenInfos);
            // 2) Create roles
            await createNewRoles(tmpTokenId, roleList);
            setInitialRoleList(roleList);
            enqueueSnackbar(t('settings:onTokenUpdate'), { variant: 'success' });
        }
        catch(e)
        {
            enqueueSnackbar(t('settings:onTokenSaveError'), { variant: 'error' });
        }
    }

    useEffect(() => {
        const init = async () =>{
            try {
              
                // Get list of all groups and add it to groupList or locally from access_token
                const groups = await getGroups();
                const filteredGroup = groups.filter((item) => item.id !== "admin");
                
                setGroupList(filteredGroup);
                if(filteredGroup.length > 0)
                    setActiveGroup(filteredGroup[0]);
                // 2) If tokenInfos exist => get list of user roles and update roleList
                if(!!tokenInfos)
                {
                    const tokens = await getBotsInfos(tokenInfos.id);
                    const filteredRoles = tokens.roles.filter((item) => item.id !== "admin")
                    console.log(filteredRoles)
                    setRoleList(filteredRoles);
                    setInitialRoleList(filteredRoles);
                    setTokenName(tokenInfos.name);
                    setChecked(tokenInfos.isAuthor);
                }

            }
            catch (e)
            {
              enqueueSnackbar(t('settings:tokensError'), { variant: 'error' });
            }
          }
          init();
    }, [tokenInfos, t, enqueueSnackbar])

    return (
        <GenericModal 
        open={open}
        handleClose={onClose}
        handleSave={onSave}
        title={tokenInfos ? tokenInfos.name : t('settings:newTokenTitle')}>
            <div className={classes.infos}>
                <TextField className={classes.idFields}
                            value={tokenName}
                            onChange={(event) => setTokenName(event.target.value as string)}
                            label={t('settings:tokenNameLabel')}
                            variant="outlined" />
                <div className={classes.checkbox}>
                    <Checkbox 
                    checked={checked}
                    onChange={() => setChecked(!checked)}
                    inputProps={{ 'aria-label': 'primary checkbox' }}/>
                    <Typography>
                        {t('settings:linkTokenLabel')}
                    </Typography>
                </div>
            </div>

           {
            <GroupsAssignmentView groupsList={groupList}
                roleList={roleList}
                selectedGroup={selectedGroup}
                onChange={onChange}
                addRole={addRoleToList}
                deleteRole={deleteRoleFromList}
                updateRole={updateRoleFromList} />
           } 
      </GenericModal>       
    )

}

export default TokenModal;


