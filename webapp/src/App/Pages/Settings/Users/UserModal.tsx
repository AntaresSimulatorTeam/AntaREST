import React, {useState, useEffect} from 'react';
import GenericModal from '../../../../components/Settings/GenericModal';
import GroupsAssignmentView from '../../../../components/Settings/GroupsAssignmentView';


interface PropTypes {
    open: boolean;
    newUser: boolean;
    onClose: () => void;
    onSave: () => void; // Ici, mettre éventuellement les données
    title: string;
};

const UserModal = (props: PropTypes) => {

    const {open, onClose, onSave, title} = props;
    const [groupList, setGroupList] = useState([]); // Which type ?
    const [roleList, setRoleList] = useState([]); // Which type ?  
    const [selectedGroup, setActiveGroup] = useState(''); // Current selected group

    const onChange = (value: string) => {
        
        setActiveGroup(value);

        // Est-ce que l'on connaît déjà tous les groupes 
        console.log('change')
    }

    const addGroup = () => {

        //1) Create a new role with empty type
        //2) Add the role in roleList
        console.log('Add group') 
    }

    const deleteGroup = (name: string) => {

        // Delete group from roleList
        console.log('Delete '+name)
    }

    const updateRoleType = (name : string, role: number) => {
        
        // 1) Find the role
        // 2) Update the type 
        console.log('Set Group Role '+name)
    }

    return (

        <GenericModal 
        open={open}
        handleClose={onClose}
        handleSave={() => onSave()}
        title={title}>
          <GroupsAssignmentView groupsList={groupList}
                                roleList={roleList}
                                selectedGroup={selectedGroup}
                                onChange={onChange}
                                addGroup={addGroup}
                                deleteGroup={deleteGroup}
                                updateRoleType={updateRoleType} />
      </GenericModal>       
    )

}

export default UserModal;


