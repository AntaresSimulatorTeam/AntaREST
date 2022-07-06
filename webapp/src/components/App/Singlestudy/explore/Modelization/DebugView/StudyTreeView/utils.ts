import IntegrationInstructionsIcon from "@mui/icons-material/IntegrationInstructions";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { SvgIconComponent } from "@mui/icons-material";
import { StudyDataType } from "../../../../../../../common/types";

export interface StudyParams {
  type: StudyDataType;
  icon: SvgIconComponent;
  data: string;
}

export const getStudyParams = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any,
  path: string,
  itemkey: string
): StudyParams | undefined => {
  if (typeof data !== "object") {
    const tmp = data.split("://");
    if (tmp && tmp.length > 0) {
      if (tmp[0] === "json") {
        return {
          type: "json",
          data: `${path}/${itemkey}`,
          icon: IntegrationInstructionsIcon,
        };
      }
      return {
        type: tmp[0] as StudyDataType,
        icon: TextSnippetIcon,
        data: `${path}/${itemkey}`,
      };
    }
    return { type: "file", icon: TextSnippetIcon, data: `${path}/${itemkey}` };
  }
  return undefined;
};

export default {};
