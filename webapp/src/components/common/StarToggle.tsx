import { Tooltip } from "@mui/material";
import StarPurple500OutlinedIcon from "@mui/icons-material/StarPurple500Outlined";
import StarOutlineOutlinedIcon from "@mui/icons-material/StarOutlineOutlined";

interface Props {
  isActive: boolean;
  activeTitle: string;
  unactiveTitle: string;
  onToggle: () => void;
}

function StarToggle(props: Props) {
  const { isActive, activeTitle, unactiveTitle, onToggle } = props;
  const StarComponent = isActive
    ? StarPurple500OutlinedIcon
    : StarOutlineOutlinedIcon;

  return (
    <Tooltip title={isActive ? activeTitle : unactiveTitle}>
      <StarComponent
        sx={{ cursor: "pointer", ml: 1 }}
        onClick={onToggle}
        color="primary"
      />
    </Tooltip>
  );
}

export default StarToggle;
