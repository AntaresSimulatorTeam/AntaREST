import { useContext, useMemo } from "react";
import { StudyMetadata } from "../../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../../redux/hooks/useAppSelector";
import { getStudyAreas } from "../../../../../../../../../redux/selectors";
import FormTable from "../../../../../../../../common/FormTable";
import SimpleLoader from "../../../../../../../../common/loaders/SimpleLoader";
import useStudyData from "../../../../../hooks/useStudyData";
import ConfigContext from "../ConfigContext";

interface Props {
  study: StudyMetadata;
  nbYears: number;
  symbol: string;
}

function Table(props: Props) {
  const { study, nbYears, symbol } = props;
  const { config, currentRuleset } = useContext(ConfigContext);
  const valuesFromConfig = config?.[currentRuleset]?.[symbol];
  const { isLoading } = useStudyData({ studyId: study.id });
  const areas = useAppSelector((state) => getStudyAreas(state, study.id));

  const defaultValues = useMemo(() => {
    const emptyCols = (Array.from({ length: nbYears }) as undefined[]).reduce(
      (acc, _, index) => {
        acc[String(index)] = undefined;
        return acc;
      },
      {} as Record<string, undefined>
    );

    return areas.reduce((acc, area) => {
      acc[area.id] = { ...emptyCols, ...valuesFromConfig?.[area.id] };
      return acc;
    }, {} as Record<string, typeof emptyCols>);
  }, [areas, nbYears, valuesFromConfig]);

  if (isLoading) {
    return <SimpleLoader />;
  }

  return (
    <FormTable
      key={JSON.stringify(defaultValues)}
      defaultValues={defaultValues}
      sx={{
        ".htPlaceholder": {
          color: "#777 !important",
        },
      }}
      tableProps={{
        type: "numeric",
        placeholder: "rand",
        allowEmpty: true,
        colHeaders: (index) => `Year ${index}`,
        width: "100%",
        height: "100%",
        stretchH: "all",
        className: "htCenter",
      }}
    />
  );
}

export default Table;
