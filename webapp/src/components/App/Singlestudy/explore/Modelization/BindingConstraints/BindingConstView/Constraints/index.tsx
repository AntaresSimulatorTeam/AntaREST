import * as R from "ramda";
import { Box } from "@mui/material";
import { useMemo } from "react";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getStudyLinks } from "../../../../../../../../redux/selectors";
import { useFormContext } from "../../../../../../../common/Form";
import { BindingConstFields, getContraintsValues } from "../utils";
import Constraint from "./Constraint";
import { LinkElement } from "../../../../../../../../common/types";

interface Props {
  bindingConst: string;
  studyId: string;
}

export function Constraints(props: Props) {
  const { bindingConst, studyId } = props;
  const { defaultValues } = useFormContext<BindingConstFields>();
  const links = useAppSelector((state) => getStudyLinks(state, studyId));
  const linksOptions: Array<LinkElement> = useMemo(() => {
    return links.map((elm) => {
      const tab = R.sort<string>(R.comparator<string>(R.lt), [
        elm.area1,
        elm.area2,
      ]);
      return { ...elm, area1: tab[0], area2: tab[1] };
    });
    /* return [
      [...new Set(sortedLinks.map((elm) => elm.area1))],
      [...new Set(sortedLinks.map((elm) => elm.area2))],
    ];*/
  }, [links]);
  const constraints = useMemo(
    () => getContraintsValues(defaultValues as Partial<BindingConstFields>),
    [defaultValues]
  );

  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        flexDirection: "column",
        mb: 1,
      }}
    >
      {Object.keys(constraints).map((key, index) => {
        return (
          <Constraint
            key={key}
            constraint={constraints[key]}
            fieldset={index > 0}
            bindingConst={bindingConst}
            studyId={studyId}
            linksOptions={linksOptions}
          />
        );
      })}
    </Box>
  );
}
