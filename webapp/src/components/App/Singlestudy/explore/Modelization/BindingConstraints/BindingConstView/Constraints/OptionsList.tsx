import { useCallback, useMemo, useState } from "react";
import { LinkClusterItem } from "../../../../../../../../common/types";
import SelectSingle from "../../../../../../../common/SelectSingle";

interface Props {
  options: Array<LinkClusterItem>;
  onChangeOption: (option1: string, option2: string) => void;
  label1: string;
  label2: string;
  value1: string;
  value2: string;
}

export default function OptionsList(props: Props) {
  const { options, label1, label2, value1, value2, onChangeOption } = props;

  const options1 = useMemo(() => {
    return options.map((elm) => elm.element);
  }, [options]);

  const options2 = useMemo(() => {
    const index = options.findIndex((elm) => elm.element.id === value1);
    if (index >= 0) return options[index].item_list;
    return [];
  }, [options, value1]);

  const [tmpValue1, setTmpValue1] = useState<string>(value1);
  const [tmpValue2, setTmpValue2] = useState<string>(value2);

  const getFirstValue2 = useCallback(
    (value: string): string => {
      const index = options.findIndex((elm) => elm.element.id === value);
      if (index >= 0) return options[index].item_list[0].id;
      return "";
    },
    [options]
  );

  const handleValue1 = (value: string): void => {
    setTmpValue1(value);
    onChangeOption(value, getFirstValue2(value));
  };

  const handleValue2 = (value: string): void => {
    setTmpValue2(value);
    onChangeOption(value1, value as string);
  };

  return (
    <>
      <SelectSingle
        name={label1}
        list={options1}
        data={tmpValue1}
        setValue={(value: string) => handleValue1(value)}
        sx={{ flexGrow: 1, height: "60px" }}
      />
      <SelectSingle
        name={label2}
        list={options2}
        data={tmpValue2} // {options2[option2Index].id}
        setValue={(value: string) => handleValue2(value)}
        sx={{ flexGrow: 1, mx: 1, height: "60px" }}
      />
    </>
  );
}
