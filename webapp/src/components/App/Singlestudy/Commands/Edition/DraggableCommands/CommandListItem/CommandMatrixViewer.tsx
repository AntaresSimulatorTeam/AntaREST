import { CommandEnum, CommandItem } from "../../commandTypes";

interface PropTypes {
  command: CommandItem;
}

function CommandMatrixViewer(props: PropTypes) {
  const { command } = props;
  const { action, args } = command;
  if (action === CommandEnum.REPLACE_MATRIX) {
    return <div>{(args as any).matrix}</div>;
  }
  return <div />;
}

export default CommandMatrixViewer;
