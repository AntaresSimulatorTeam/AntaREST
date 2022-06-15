import { Box } from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../common/Fieldset";
import { AutoSubmitHandler, FormObj } from "../../../../../common/Form";
import { getLinkPath, LinkFields } from "./utils";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import {
  LinkElement,
  MatrixStats,
  StudyMetadata,
} from "../../../../../../common/types";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import MatrixInput from "../../../../../common/MatrixInput";
import LinkMatrixView from "./LinkMatrixView";

export default function LinkForm(
  props: FormObj<LinkFields, unknown> & {
    link: LinkElement;
    study: StudyMetadata;
  }
) {
  const { register, defaultValues, study, link } = props;
  const studyId = study.id;
  const isTabMatrix = useMemo((): boolean => {
    let version = 0;
    try {
      version = parseInt(study.version, 10);
    } catch (e) {
      version = 0;
    }
    return version >= 820;
  }, [study]);

  const { area1, area2 } = link;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const path = useMemo(() => {
    return getLinkPath(area1, area2);
  }, [area1, area2]);

  const optionTransCap = ["infinite", "ignore", "enabled"].map((item) => ({
    label: t(`study.modelization.links.transmissionCapa.${item}`),
    value: item.toLowerCase(),
  }));

  const optionType = ["ac", "dc", "gaz", "virt", "other"].map((item) => ({
    label: t(`study.modelization.links.type.${item}`),
    value: item.toLowerCase(),
  }));

  const filterOptions = ["hourly", "daily", "weekly", "monthly", "annual"].map(
    (item) => ({
      label: t(`study.${item}`),
      value: item,
    })
  );

  const columnsNames = [
    t("study.modelization.links.matrix.columns.transCapaDirect"),
    t("study.modelization.links.matrix.columns.transCapaIndirect"),
    t("study.modelization.links.matrix.columns.hurdleCostsDirect"),
    t("study.modelization.links.matrix.columns.hurdleCostsIndirect"),
    t("study.modelization.links.matrix.columns.inpedances"),
    t("study.modelization.links.matrix.columns.loopFlow"),
    t("study.modelization.links.matrix.columns.pShiftMin"),
    t("study.modelization.links.matrix.columns.pShiftMax"),
  ];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleAutoSubmit = async (path: string, data: any) => {
    try {
      await editStudy(data, studyId, path);
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const handleTypeAutoSubmit: AutoSubmitHandler<LinkFields, string> = (
    value
  ) => {
    const defaultFilterSynthesis = defaultValues?.filterSynthesis
      ? (defaultValues?.filterSynthesis as Array<string>).filter(
          (elm) => elm !== ""
        )
      : [];
    const defaultFilterByYear = defaultValues?.filterByYear
      ? (defaultValues?.filterByYear as Array<string>).filter(
          (elm) => elm !== ""
        )
      : [];

    const common = {
      "hurdles-cost": defaultValues?.hurdleCost,
      "loop-flow": defaultValues?.loopFlows,
      "use-phase-shifter": defaultValues?.pst,
      "transmission-capacities": defaultValues?.transmissionCapa,
      "filter-synthesis": defaultFilterSynthesis.join(","),
      "filter-year-by-year": defaultFilterByYear.join(","),
    };

    let other = {
      "asset-type": "other",
      "link-style": "dot",
      "link-width": 2,
      colorr: 255,
      colorg: 128,
      colorb: 0,
    };
    switch (value) {
      case "ac":
        other = {
          "asset-type": "ac",
          "link-style": "plain",
          "link-width": 1,
          colorr: 112,
          colorg: 112,
          colorb: 112,
        };
        break;

      case "dc":
        other = {
          "asset-type": "dc",
          "link-style": "dash",
          "link-width": 2,
          colorr: 0,
          colorg: 255,
          colorb: 0,
        };
        break;

      case "gaz":
        other = {
          "asset-type": "gaz",
          "link-style": "plain",
          "link-width": 3,
          colorr: 0,
          colorg: 128,
          colorb: 255,
        };
        break;

      case "virt":
        other = {
          "asset-type": "virt",
          "link-style": "dotdash",
          "link-width": 2,
          colorr: 255,
          colorg: 0,
          colorb: 128,
        };
        break;

      default:
        break;
    }
    handleAutoSubmit(path.type, { ...common, ...other });
  };

  const renderSelect = (
    filterName: string,
    options: Array<{ label: string; value: string }>,
    onAutoSubmit?: AutoSubmitHandler<LinkFields, string>
  ) => (
    <Box sx={{ display: "flex", flexGrow: 1 }}>
      <SelectFE
        {...register(filterName, {
          onAutoSubmit:
            onAutoSubmit ||
            ((value) => {
              handleAutoSubmit(path[filterName], value);
            }),
        })}
        defaultValue={(defaultValues || {})[filterName] || []}
        variant="filled"
        options={options}
        formControlProps={{
          sx: {
            flex: 1,
            mx: 2,
            boxSizing: "border-box",
          },
        }}
        sx={{ width: "100%", minWidth: "200px" }}
        label={t(`study.modelization.links.${filterName}`)}
      />
    </Box>
  );
  const renderFilter = (filterName: string) => (
    <Box sx={{ mb: 2 }}>
      <SelectFE
        multiple
        {...register(filterName, {
          onAutoSubmit: (value) => {
            const selection = value
              ? (value as Array<string>).filter((val) => val !== "")
              : [];
            handleAutoSubmit(path[filterName], selection.join(", "));
          },
        })}
        renderValue={(value: unknown) => {
          const selection = value
            ? (value as Array<string>).filter((val) => val !== "")
            : [];
          return selection.length > 0
            ? selection.map((elm) => t(`study.${elm}`)).join(", ")
            : t("global.none");
        }}
        defaultValue={(defaultValues || {})[filterName] || []}
        variant="filled"
        options={filterOptions}
        sx={{ minWidth: "200px" }}
        label={t(`study.modelization.nodeProperties.${filterName}`)}
      />
    </Box>
  );

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        py: 2,
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Fieldset title={t("global.general")} style={{ padding: "16px" }}>
          <Box
            sx={{
              width: "100%",
              display: "flex",
              justifyContent: "flex-start",
            }}
          >
            <SwitchFE
              label={t("study.modelization.links.hurdleCost")}
              {...register("hurdleCost", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(path.hurdleCost, value),
              })}
            />
            <SwitchFE
              sx={{ mx: 2 }}
              label={t("study.modelization.links.loopFlows")}
              {...register("loopFlows", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(path.loopFlows, value),
              })}
            />
            <SwitchFE
              sx={{ mx: 2 }}
              label={t("study.modelization.links.pst")}
              {...register("pst", {
                onAutoSubmit: (value) => handleAutoSubmit(path.pst, value),
              })}
            />
            {renderSelect("transmissionCapa", optionTransCap)}
            {renderSelect("type", optionType, handleTypeAutoSubmit)}
          </Box>
        </Fieldset>
        <Fieldset
          title={t("study.modelization.nodeProperties.outputFilter")}
          style={{ padding: "16px" }}
        >
          <Box
            sx={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          >
            {renderFilter("filterSynthesis")}
            {renderFilter("filterByYear")}
          </Box>
        </Fieldset>
        <Box
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            height: "500px",
          }}
        >
          {isTabMatrix ? (
            <LinkMatrixView study={study} area1={area1} area2={area2} />
          ) : (
            <MatrixInput
              study={study}
              url={`input/links/${area1.toLowerCase()}/${area2.toLowerCase()}`}
              columnsNames={columnsNames}
              computStats={MatrixStats.NOCOL}
            />
          )}
        </Box>
      </Box>
    </Box>
  );
}
