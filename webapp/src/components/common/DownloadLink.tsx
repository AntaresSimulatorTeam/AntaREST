import { IconButton, Tooltip } from "@mui/material";
import { ReactElement } from "react";
import { refresh } from "../../redux/ducks/auth";
import { useAppDispatch, useAppSelector } from "../../redux/hooks";
import { getAuthUser } from "../../redux/selectors";

interface Props {
  url: string;
  title: string;
  children: ReactElement;
}

function DownloadLink(props: Props) {
  const { children, url, title } = props;
  const user = useAppSelector(getAuthUser);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = async () => {
    if (user) {
      await dispatch(refresh()).unwrap();
    }
    // eslint-disable-next-line no-restricted-globals
    location.href = url;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <IconButton style={{ cursor: "pointer" }} onClick={handleClick}>
      <Tooltip title={title}>{children}</Tooltip>
    </IconButton>
  );
}

export default DownloadLink;
