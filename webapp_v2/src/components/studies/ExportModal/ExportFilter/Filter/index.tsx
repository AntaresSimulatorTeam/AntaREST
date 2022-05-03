import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { TextField } from "@mui/material";
import {
  Area,
  Set,
  StudyOutputDownloadType,
} from "../../../../../common/types";
import SelectMulti from "../../../../common/SelectMulti";
import { Root } from "./style";
import MultipleLinkElement from "./MultipleLinkElement";
import SingleLinkElement from "./SingleLinkElement";

interface PropTypes {
  type: StudyOutputDownloadType;
  areas: { [elm: string]: Area };
  sets: { [elm: string]: Set };
  filterValue: Array<string>;
  setFilterValue: (elm: Array<string>) => void;
  filterInValue: string;
  setFilterInValue: (elm: string) => void;
  filterOutValue: string;
  setFilterOutValue: (elm: string) => void;
}

function Filter(props: PropTypes) {
  const [t] = useTranslation();
  const {
    type,
    areas,
    sets,
    filterValue,
    filterInValue,
    filterOutValue,
    setFilterValue,
    setFilterInValue,
    setFilterOutValue,
  } = props;
  const [areasOrDistrictsList, setAreasOrDistrictsList] = useState<
    Array<string>
  >([]);

  useEffect(() => {
    const getAreasOrDistrictsList = (): Array<string> => {
      let res: Array<string> = [];
      switch (type) {
        case StudyOutputDownloadType.AREA:
          res = Object.keys(areas);
          break;

        case StudyOutputDownloadType.DISTRICT:
          res = Object.keys(sets);
          break;

        default:
          break;
      }
      return res;
    };
    setAreasOrDistrictsList(getAreasOrDistrictsList());
  }, [areas, sets, type]);

  return type !== StudyOutputDownloadType.LINK ? (
    <Root>
      <SelectMulti
        name={`${t("singlestudy:filter")} *`}
        list={areasOrDistrictsList.map((elm) => ({ id: elm, name: elm }))}
        data={filterValue}
        setValue={(elm: Array<string> | string) =>
          setFilterValue(elm as Array<string>)
        }
        sx={{ m: 0, mb: 2, width: "95%" }}
      />
      <TextField
        label={t("singlestudy:filterIn")}
        value={filterInValue}
        onChange={(event) => setFilterInValue(event.target.value)}
        sx={{ m: 0, mb: 2, width: "95%" }}
      />
      <TextField
        label={t("singlestudy:filterOut")}
        value={filterOutValue}
        onChange={(event) => setFilterOutValue(event.target.value)}
        sx={{ m: 0, mb: 2, width: "95%", bgcolor: "red" }}
      />
    </Root>
  ) : (
    <Root>
      <MultipleLinkElement
        label={t("singlestudy:filter")}
        areas={Object.keys(areas)}
        values={filterValue}
        onChange={setFilterValue}
      />
      <SingleLinkElement
        label={t("singlestudy:filterIn")}
        areas={Object.keys(areas)}
        onChange={setFilterInValue}
      />
      <SingleLinkElement
        label={t("singlestudy:filterOut")}
        areas={Object.keys(areas)}
        onChange={setFilterOutValue}
      />
    </Root>
  );
}

export default Filter;
