import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getAreas } from "../../../../../../../../redux/selectors";
import { DynamicListProps } from "../../../../../../../common/DynamicList";
import { AreaCoefficientItem } from "../utils";

export function useAreasOptions(
  fields: AreaCoefficientItem[]
): DynamicListProps["options"] {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();

  const areas = useAppSelector((state) => getAreas(state, studyId));

  const options = useMemo(() => {
    const areaIds = fields.map((field) => field.areaId);
    return areas
      .filter((area) => !areaIds.includes(area.id))
      .map((area) => ({
        label: area.name,
        value: area.id,
      }));
  }, [areas, fields]);

  return options;
}
