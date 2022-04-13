/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
import { ReactNode } from "react";
import { connect, ConnectedProps } from "react-redux";
import { loginUser, logoutAction } from "../../store/auth";
import { refresh } from "../../services/api/auth";
import { AppState } from "../../store/reducers";

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
  children?: ReactNode;
}
type PropTypes = PropsFromRedux & OwnProps;

function DownloadLink(props: PropTypes) {
  const { user, login, logout, children, url } = props;

  const handleClick = async () => {
    if (user) {
      await refresh(user, login, logout);
    }
    // eslint-disable-next-line no-restricted-globals
    location.href = url;
  };

  return (
    <span style={{ cursor: "pointer" }} onClick={handleClick}>
      {children}
    </span>
  );
}

DownloadLink.defaultProps = {
  children: null,
};

export default connector(DownloadLink);
