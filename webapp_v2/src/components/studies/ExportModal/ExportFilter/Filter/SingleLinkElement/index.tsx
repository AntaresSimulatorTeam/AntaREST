import { TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import SelectSingle from "../../../../../common/SelectSingle";
import { LinkContainer } from "../style";
import { LinkFilter } from "./style";

interface FilterLink {
  area1: string;
  area2: string;
}

export default function SingleLinkElement(props: {
  globalFilter?: boolean;
  label: string;
  areas: Array<string>;
  onChange: (value: string) => void;
}) {
  const [t] = useTranslation();
  const { globalFilter, label, areas, onChange } = props;
  const [link, setLink] = useState<FilterLink>({ area1: "", area2: "" });

  const onSelectChange = (id: number, elm: string): void => {
    let { area1, area2 } = link;
    if (id === 0) {
      area1 = elm;
      setLink({ ...link, area1: elm });
    } else {
      area2 = elm;
      setLink({ ...link, area2: elm });
    }
    onChange(`${area1}^${area2}`);
  };
  return (
    <LinkContainer>
      <Typography
        sx={{ width: "auto", height: "auto", mr: 1, bgcolor: "gray" }}
      >
        {label}:
      </Typography>
      {globalFilter === true ? (
        <LinkFilter>
          <SelectSingle
            name={`${t("singlestudy:area")}1 *`}
            list={areas.map((elm) => ({ id: elm, name: elm }))}
            data={link.area1}
            setValue={(elm: Array<string> | string) =>
              onSelectChange(0, elm as string)
            }
            sx={{ flexGrow: 1, mx: 1 }}
          />
          <SelectSingle
            name={`${t("singlestudy:area")}2 *`}
            list={areas.map((elm) => ({ id: elm, name: elm }))}
            data={link.area1}
            setValue={(elm: Array<string> | string) =>
              onSelectChange(1, elm as string)
            }
            sx={{ width: "50%" }}
          />
        </LinkFilter>
      ) : (
        <LinkFilter>
          <TextField
            label={`${t("singlestudy:area")} 1`}
            value={link.area1}
            onChange={(event) => onSelectChange(0, event.target.value)}
            sx={{ mx: 1 }}
          />
          <TextField
            label={`${t("singlestudy:area")} 2`}
            value={link.area2}
            onChange={(event) => onSelectChange(1, event.target.value)}
          />
        </LinkFilter>
      )}
    </LinkContainer>
  );
}

SingleLinkElement.defaultProps = {
  globalFilter: false,
};
