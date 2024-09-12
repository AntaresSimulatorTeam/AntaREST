import {
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
} from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import {
  getFileIcon,
  getFileType,
  type TreeFolder,
  type DataCompProps,
} from "../utils";
import { Fragment } from "react";
import EmptyView from "../../../../../common/page/SimpleContent";
import { useTranslation } from "react-i18next";

function Folder({
  filename,
  filePath,
  treeData,
  setSelectedFile,
}: DataCompProps) {
  const { t } = useTranslation();
  const list = Object.entries(treeData as TreeFolder);

  return (
    <List
      subheader={<ListSubheader>{filename}</ListSubheader>}
      sx={{
        height: 1,
        overflow: "auto",
      }}
      dense
    >
      {list.length > 0 ? (
        list.map(([filename, data], index, arr) => {
          const fileType = getFileType(data);
          const Icon = getFileIcon(fileType);
          const isLast = index === arr.length - 1;

          return (
            <Fragment key={filename}>
              <ListItemButton
                onClick={() =>
                  setSelectedFile({
                    fileType,
                    filename,
                    filePath: `${filePath}/${filename}`,
                    treeData: data,
                  })
                }
              >
                <ListItemIcon>
                  <Icon />
                </ListItemIcon>
                <ListItemText primary={filename} />
              </ListItemButton>
              {!isLast && <Divider variant="fullWidth" />}
            </Fragment>
          );
        })
      ) : (
        <EmptyView title={t("study.debug.folder.empty")} icon={FolderIcon} />
      )}
    </List>
  );
}

export default Folder;
