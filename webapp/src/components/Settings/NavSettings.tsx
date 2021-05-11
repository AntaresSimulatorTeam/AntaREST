import React from 'react';
import { makeStyles, createStyles, Theme } from '@material-ui/core';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';

const useStyles = makeStyles((theme: Theme) => createStyles({
    root: {
      flex: '0 0 20%',
      minWidth: '200px',
      height: '100%',
      overflow: 'auto',
      borderRight: `4px solid ${theme.palette.primary.dark}`,
      backgroundColor: theme.palette.primary.main
    },
    userInfos : {
      width: '100%',
      padding: '10px 20px',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: theme.palette.primary.dark,
      color: 'white'
    },
    list: {
      padding: '10px 20px',
      alignItems: 'center'
    },
    item : {
      backgroundColor: theme.palette.primary.main,
      marginTop: theme.spacing(1),
      '&:hover':{
        backgroundColor: theme.palette.primary.dark
      }
    },
    itemSelected : {
      backgroundColor: theme.palette.secondary.main,
      marginTop: theme.spacing(1),
      '&:hover':{
        backgroundColor: theme.palette.secondary.main
      }
    },
    itemText :{
      color: 'white',
    }

}));
  
interface PropTypes {
    items: Array<string>,
    currentItem: String,
    onItemClick: (item : string) => void
}

const NavSettings = (props: PropTypes) => {

    const classes = useStyles();
    const {currentItem, items, onItemClick} = props;

    return (
    <div className={classes.root}>
        <List className={classes.list}>
          {
            items.map((item : string, index : number) => 
                <ListItem button key={item} onClick={() => onItemClick(item)} className={currentItem === item ? classes.itemSelected: classes.item}>
                    <ListItemText primary={item} className={classes.itemText} />
                </ListItem>
            )
          }
        </List>   
    </div>
    );

}

export default NavSettings
