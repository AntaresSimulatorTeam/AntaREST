import { Menu, MenuItem, ListItemIcon, ListItemText } from "@mui/material";
import { SvgIconComponent } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

export interface ActionsMenuItem {
  key: string;
  icon: SvgIconComponent;
  action: VoidFunction | (() => Promise<void>);
  condition?: boolean;
  color?: string;
}

interface Props {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: VoidFunction;
  items: ActionsMenuItem[];
}

function ActionsMenu({ anchorEl, open, onClose, items }: Props) {
  const [t] = useTranslation();

  return (
    <Menu anchorEl={anchorEl} keepMounted open={open} onClose={onClose}>
      {items.map(
        (item) =>
          item.condition && (
            <MenuItem
              onClick={() => {
                item.action();
                onClose();
              }}
              key={item.key}
            >
              <ListItemIcon>
                <item.icon
                  sx={{
                    color: item.color,
                    width: "24px",
                    height: "24px",
                  }}
                />
              </ListItemIcon>
              <ListItemText sx={{ color: item.color }}>
                {t(item.key)}
              </ListItemText>
            </MenuItem>
          )
      )}
    </Menu>
  );
}

export default ActionsMenu;
