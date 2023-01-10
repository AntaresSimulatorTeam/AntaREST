import { useEffect, useState } from "react";
import { StudyMetadata } from "../../../../../../../../../common/types";
import useStudySynthesis from "../../../../../../../../../redux/hooks/useStudySynthesis";
import { getAreas } from "../../../../../../../../../redux/selectors";
import PropertiesView from "../../../../../../../../common/PropertiesView";
import SplitLayoutView from "../../../../../../../../common/SplitLayoutView";
import UsePromiseCond from "../../../../../../../../common/utils/UsePromiseCond";
import ListElement from "../../../../../common/ListElement";
import Table from "./Table";

interface Props {
  study: StudyMetadata;
  nbYears: number;
}

function Thermal(props: Props) {
  const { study, nbYears } = props;
  const res = useStudySynthesis({
    studyId: study.id,
    selector: getAreas,
  });

  const [selectedAreaId, setSelectedAreaId] = useState("");

  useEffect(
    () => {
      const { data } = res;
      setSelectedAreaId(data && data.length > 0 ? data[0].id : "");
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [res.data]
  );

  return (
    <UsePromiseCond
      response={res}
      ifResolved={(areas) => (
        <SplitLayoutView
          sx={{
            height: 1,
            ".SplitLayoutView__Left": { pl: 0 },
          }}
          left={
            <PropertiesView
              mainContent={
                <ListElement
                  sx={{ p: 0 }}
                  list={areas}
                  currentElement={selectedAreaId}
                  currentElementKeyToTest="id"
                  setSelectedItem={({ id }) => setSelectedAreaId(id)}
                />
              }
            />
          }
          right={
            <Table
              study={study}
              nbYears={nbYears}
              symbol="t"
              rowType="thermal"
              areaId={selectedAreaId}
            />
          }
        />
      )}
    />
  );
}

export default Thermal;
