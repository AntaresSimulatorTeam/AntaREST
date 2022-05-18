import { connect, ConnectedProps } from "react-redux";
import { IconButton, Tooltip } from "@mui/material";
import { ReactElement } from "react";
import { getAuthUser } from "../../redux/selectors";
import { AppState } from "../../redux/ducks";
import { refresh } from "../../redux/ducks/auth";

const mapState = (state: AppState) => ({
  user: getAuthUser(state),
});

const mapDispatch = {
  refresh,
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
  const { user, refresh, children, url, title } = props;

  const handleClick = async () => {
    if (user) {
      await refresh().unwrap();
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
