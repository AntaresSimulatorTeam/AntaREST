import { connect, ConnectedProps } from "react-redux";
import { loginUser, logoutAction } from "../../redux/ducks/auth";
import { IconButton, Tooltip } from "@mui/material";
import { ReactElement } from "react";
import { refresh } from "../../services/api/auth";
import { AppState } from "../../redux/ducks";

const mapState = (state: AppState) => ({
  user: state.auth.user,
});

const mapDispatch = {
  login: loginUser,
  logout: logoutAction,
};

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;

interface OwnProps {
  url: string;
  title: string;
  children: ReactElement;
}
type PropTypes = PropsFromRedux & OwnProps;

function DownloadLink(props: PropTypes) {
  const { user, title, login, logout, children, url } = props;

  const handleClick = async () => {
    if (user) {
      await refresh(user, login, logout);
    }
    // eslint-disable-next-line no-restricted-globals
    location.href = url;
  };

  return (
    <IconButton style={{ cursor: "pointer" }} onClick={handleClick}>
      <Tooltip title={title}>{children}</Tooltip>
    </IconButton>
  );
}

export default connector(DownloadLink);
