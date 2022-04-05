/* eslint-disable react-hooks/exhaustive-deps */
import { useNavigate } from "react-router-dom";
import { Box } from "@mui/material";
import Split from "react-split";
import { StudyMetadata, VariantTree } from "../../../common/types";
import "./Split.css";
import StudyTreeView from "./StudyTreeView";
import InformationView from "./InformationView";

interface Props {
  study: StudyMetadata | undefined;
  parents: Array<StudyMetadata>;
  childrenTree: VariantTree | undefined;
}

function HomeView(props: Props) {
  const navigate = useNavigate();
  const { study, parents, childrenTree } = props;

  return (
    <Split
      className="split"
      gutterSize={4}
      snapOffset={0}
      sizes={[36, 64]}
      style={{
        display: "flex",
        flexDirection: "row",
        flex: 1,
      }}
    >
      <Box
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="flex-start"
        boxSizing="border-box"
        overflow="hidden"
        px={2}
      >
        <StudyTreeView
          study={study}
          parents={parents}
          childrenTree={childrenTree}
          onClick={(studyId: string) => navigate(`/studies/${studyId}`)}
        />
      </Box>
      <Box
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        boxSizing="border-box"
        overflow="hidden"
      >
        <InformationView study={study} />
      </Box>
    </Split>
  );
}

export default HomeView;
