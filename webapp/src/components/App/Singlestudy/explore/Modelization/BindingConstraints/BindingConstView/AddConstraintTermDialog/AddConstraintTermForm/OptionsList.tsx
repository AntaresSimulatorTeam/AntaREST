import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { AllClustersAndLinks } from "../../../../../../../../../common/types";
import SelectFE from "../../../../../../../../common/fieldEditors/SelectFE";
import { ControlPlus } from "../../../../../../../../common/Form";
import { ConstraintType } from "../../utils";

interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  control: ControlPlus<ConstraintType, any>;
}

export default function OptionsList(props: Props) {
  const { list, isLink, control } = props;
  const [t] = useTranslation();
  const name1 = useMemo(() => (isLink ? "area1" : "area"), [isLink]);
  const name2 = useMemo(() => (isLink ? "area2" : "cluster"), [isLink]);
  const options = useMemo(
    () => (isLink ? list.links : list.clusters),
    [isLink, list.clusters, list.links]
  );
  const options1 = useMemo(() => {
    return options.map((elm) => ({
      label: elm.element.name,
      value: elm.element.id,
    }));
  }, [options, isLink]);
  const [options2, setOptions2] = useState<
    Array<{ label: string; value: string }>
  >([]);

  const getOption2 = (value: string) => {
    const index = options.findIndex((elm) => elm.element.id === value);
    if (index >= 0)
      setOptions2(
        options[index].item_list.map((elm) => ({
          label: elm.name,
          value: elm.id,
        }))
      );
    return [];
  };

  return (
    <>
      <SelectFE
        name={`data.${name1}`}
        label={t(`study.${name1}`)}
        options={options1}
        control={control}
        onChange={(e) => getOption2(e.target.value as string)}
        rules={{
          required: t("form.field.required") as string,
        }}
        sx={{ flexGrow: 1, height: "60px" }}
      />
      <SelectFE
        name={`data.${name2}`}
        label={t(`study.${name2}`)}
        options={options2}
        control={control}
        rules={{
          required: t("form.field.required") as string,
        }}
        sx={{ flexGrow: 1, height: "60px" }}
      />
    </>
  );
}
