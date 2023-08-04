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
  openMenu: string;
  onClose: () => void;
  items: ActionsMenuItem[];
}

function ActionsMenu({ anchorEl, openMenu, onClose, items }: Props) {
  const [t] = useTranslation();

  return (
    <Menu
      id="menu-study"
      anchorEl={anchorEl}
      keepMounted
      open={openMenu === "menu-study"}
      onClose={onClose}
    >
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
