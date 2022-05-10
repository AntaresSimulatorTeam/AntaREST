/* eslint-disable camelcase */
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import _ from "lodash";
import { Box, Checkbox, FormControlLabel, styled } from "@mui/material";
import {
  Area,
  Set as District,
  FileStudyTreeConfigDTO,
  StudyOutputDownloadDTO,
  StudyOutputDownloadLevelDTO,
  StudyOutputDownloadType,
} from "../../../../common/types";
import Filter from "./Filter";
import TagSelect from "./TagSelect";
import SelectSingle from "../../../common/SelectSingle";
import SelectMulti from "../../../common/SelectMulti";
import { scrollbarStyle } from "../../../../theme";

const Root = styled(Box)(({ theme }) => ({
  flex: 1,
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  overflowX: "hidden",
  overflowY: "auto",
  padding: theme.spacing(1, 0),
  ...scrollbarStyle,
}));

interface PropTypes {
  output: string;
  synthesis: FileStudyTreeConfigDTO | undefined;
  filter: StudyOutputDownloadDTO;
  setFilter: (filter: StudyOutputDownloadDTO) => void;
}

function ExportFilterModal(props: PropTypes) {
  const [t] = useTranslation();
  const { output, synthesis, filter, setFilter } = props;
  const [year, setCurrentYear] = useState<Array<number>>([]);
  const [byYear, setByYear] = useState<{ isByYear: boolean; nbYear: number }>({
    isByYear: false,
    nbYear: -1,
  });
  const [areaList, setAreaList] = useState<{ [elm: string]: Area }>({});
  const [districtList, setDistrictList] = useState<{ [elm: string]: District }>(
    {}
  );

  const typeList: Array<string> = [
    StudyOutputDownloadType.AREAS,
    StudyOutputDownloadType.LINKS,
    StudyOutputDownloadType.DISTRICT,
  ];
  const levelList: Array<string> = [
    StudyOutputDownloadLevelDTO.HOURLY,
    StudyOutputDownloadLevelDTO.DAILY,
    StudyOutputDownloadLevelDTO.WEEKLY,
    StudyOutputDownloadLevelDTO.MONTHLY,
    StudyOutputDownloadLevelDTO.ANNUAL,
  ];

  const onTypeChange = (value: Array<string> | string): void => {
    setFilter({
      ...filter,
      filter: [],
      filterIn: "",
      filterOut: "",
      type: value as StudyOutputDownloadType,
    });
  };

  const onLevelChange = (value: Array<string> | string): void => {
    setFilter({ ...filter, level: value as StudyOutputDownloadLevelDTO });
  };

  useEffect(() => {
    if (synthesis) {
      if (output in synthesis.outputs) {
        const outputs = synthesis.outputs[output];
        setByYear({ isByYear: outputs?.by_year, nbYear: outputs?.nbyears });
        setAreaList(synthesis.areas);
        setDistrictList(synthesis.sets);
      }
    }
  }, [synthesis, output]);

  return (
    <Root>
      <SelectSingle
        name={t("singlestudy:type")}
        list={typeList.map((elm) => ({
          id: elm,
          name: t(`singlestudy:${elm.toLowerCase()}`),
        }))}
        data={filter.type}
        setValue={(data: string) => onTypeChange(data)}
        sx={{ width: "300px", mb: 2 }}
        required
      />
      {byYear.isByYear && byYear.nbYear > 0 && (
        <SelectMulti
          name={t("singlestudy:years")}
          list={_.range(byYear.nbYear).map((elm) => ({
            id: elm.toString(),
            name: elm.toString(),
          }))}
          data={year.map((elm) => elm.toString())}
          setValue={(value: Array<string> | string) =>
            setCurrentYear(
              (value as Array<string>).map((elm) => parseInt(elm, 10))
            )
          }
          sx={{ width: "100%", mb: 2 }}
          required
        />
      )}
      <SelectSingle
        name={t("singlestudy:level")}
        list={levelList.map((elm) => ({
          id: elm,
          name: t(`singlestudy:${elm.toLowerCase()}`),
        }))}
        data={filter.level}
        setValue={(data: string) => onLevelChange(data)}
        sx={{ width: "300px", mb: 2 }}
      />
      <TagSelect
        label={t("singlestudy:columns")}
        values={filter.columns !== undefined ? filter.columns : []}
        onChange={(value: Array<string>) =>
          setFilter({ ...filter, columns: value })
        }
      />
      <Filter
        type={filter.type}
        areas={areaList}
        sets={districtList}
        filterValue={filter.filter ? filter.filter : []}
        setFilterValue={(elm: Array<string>) =>
          setFilter({ ...filter, filter: elm })
        }
        filterInValue={filter.filterIn ? filter.filterIn : ""}
        setFilterInValue={(elm: string) =>
          setFilter({ ...filter, filterIn: elm })
        }
        filterOutValue={filter.filterOut ? filter.filterOut : ""}
        setFilterOutValue={(elm: string) =>
          setFilter({ ...filter, filterOut: elm })
        }
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={filter.synthesis}
            onChange={(e, checked) =>
              setFilter({ ...filter, synthesis: checked })
            }
            name={t("singlestudy:synthesis")}
          />
        }
        sx={{ my: 1 }}
        label={t("singlestudy:synthesis")}
      />
      <FormControlLabel
        control={
          <Checkbox
            checked={filter.includeClusters}
            onChange={(e, checked) =>
              setFilter({ ...filter, includeClusters: checked })
            }
            name={t("singlestudy:includeClusters")}
          />
        }
        label={t("singlestudy:includeClusters")}
      />
    </Root>
  );
}

export default ExportFilterModal;
