import { Paper } from "@mui/material";
import { connect, ConnectedProps } from "react-redux";
import { StudyMetadata } from "../../../../common/types";
import {
  addListener,
  removeListener,
  subscribe,
  unsubscribe,
} from "../../../../store/websockets";

interface OwnTypes {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
}

const mapState = () => ({});

const mapDispatch = {
  subscribeChannel: subscribe,
  unsubscribeChannel: unsubscribe,
  addWsListener: addListener,
  removeWsListener: removeListener,
};

const connector = connect(mapState, mapDispatch);
type ReduxProps = ConnectedProps<typeof connector>;
type PropTypes = ReduxProps & OwnTypes;

function LauncherHistory(props: PropTypes) {
  const { study } = props;

  return (
    <Paper
      sx={{
        flex: 1,
        bgcolor: "rgba(36, 207, 157, 0.05)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        boxSizing: "border-box",
        mr: 1,
        p: 2,
      }}
    >
      {study && study.name}
    </Paper>
  );
}

export default connector(LauncherHistory);
