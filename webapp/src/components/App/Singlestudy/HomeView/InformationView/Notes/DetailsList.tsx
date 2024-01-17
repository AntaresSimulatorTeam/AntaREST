import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Avatar from "@mui/material/Avatar";
import { Icon } from "@mui/material";
import { SvgIconComponent } from "@mui/icons-material";

interface ListItem {
  content: string | number;
  label: string;
  icon: SvgIconComponent;
  iconColor?: string;
}

interface Props {
  items: ListItem[];
}

function DetailsList({ items }: Props) {
  return (
    <List
      sx={{
        width: 1,
        backgroundColor: "#222333",
      }}
    >
      {items.map((item) => (
        <ListItem key={item.label} sx={{ py: 0 }}>
          <ListItemAvatar>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                backgroundColor: item.iconColor || "default",
              }}
            >
              <Icon
                component={item.icon}
                sx={{
                  width: 20,
                  height: 20,
                }}
              />
            </Avatar>
          </ListItemAvatar>
          <ListItemText primary={item.content} secondary={item.label} />
        </ListItem>
      ))}
    </List>
  );
}

export default DetailsList;
