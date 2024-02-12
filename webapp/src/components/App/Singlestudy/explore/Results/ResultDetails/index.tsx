import {
  Box,
  Button,
  Paper,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  ToggleButtonGroupProps,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useOutletContext, useParams } from "react-router";
import axios from "axios";
import GridOffIcon from "@mui/icons-material/GridOff";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import {
  Area,
  LinkElement,
  MatrixType,
  StudyMetadata,
} from "../../../../../../common/types";
import usePromise from "../../../../../../hooks/usePromise";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getLinks,
  getStudyOutput,
} from "../../../../../../redux/selectors";
import { getStudyData } from "../../../../../../services/api/study";
import { isSearchMatching } from "../../../../../../utils/stringUtils";
import EditableMatrix from "../../../../../common/EditableMatrix";
import PropertiesView from "../../../../../common/PropertiesView";
import SplitLayoutView from "../../../../../common/SplitLayoutView";
import ListElement from "../../common/ListElement";
import {
  createPath,
  DataType,
  MAX_YEAR,
  OutputItemType,
  SYNTHESIS_ITEMS,
  Timestep,
} from "./utils";
import UsePromiseCond, {
  mergeResponses,
} from "../../../../../common/utils/UsePromiseCond";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { downloadMatrix } from "../../../../../../utils/matrixUtils";
import ButtonBack from "../../../../../common/ButtonBack";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";

function ResultDetails() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { outputId } = useParams();

  const outputRes = useStudySynthesis({
    studyId: study.id,
    selector: (state, id) => getStudyOutput(state, id, outputId as string),
  });

  const { data: output } = outputRes;
  const [dataType, setDataType] = useState(DataType.General);
  const [timestep, setTimeStep] = useState(Timestep.Hourly);
  const [year, setYear] = useState(-1);
  const [itemType, setItemType] = useState(OutputItemType.Areas);
  const [selectedItemId, setSelectedItemId] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const isSynthesis = itemType === OutputItemType.Synthesis;
  const { t } = useTranslation();
  const navigate = useNavigate();

  const items = useAppSelector((state) =>
    itemType === OutputItemType.Areas
      ? getAreas(state, study.id)
      : getLinks(state, study.id),
  ) as Array<{ id: string; name: string; label?: string }>;

  const filteredItems = useMemo(() => {
    return isSynthesis
      ? SYNTHESIS_ITEMS
      : items.filter((item) =>
          isSearchMatching(searchValue, item.label || item.name),
        );
  }, [isSynthesis, items, searchValue]);

  const selectedItem = filteredItems.find(
    (item) => item.id === selectedItemId,
  ) as (Area & { id: string }) | LinkElement | undefined;

  const maxYear = output?.nbyears ?? MAX_YEAR;

  useEffect(
    () => {
      const isValidSelectedItem =
        !!selectedItemId &&
        filteredItems.find((item) => item.id === selectedItemId);

      if (!isValidSelectedItem) {
        setSelectedItemId(filteredItems.length > 0 ? filteredItems[0].id : "");
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filteredItems],
  );

  const matrixRes = usePromise<MatrixType | null>(
    async () => {
      if (output && selectedItem && !isSynthesis) {
        const path = createPath({
          output,
          item: selectedItem,
          dataType,
          timestep,
          year,
        });

        const res = await getStudyData(study.id, path);
        if (typeof res === "string") {
          const fixed = res
            .replace(/NaN/g, '"NaN"')
            .replace(/Infinity/g, '"Infinity"');

          return JSON.parse(fixed);
        }
        return res;
      }
      return null;
    },
    {
      resetDataOnReload: true,
      resetErrorOnReload: true,
      deps: [study.id, output, selectedItem, dataType, timestep, year],
    },
  );

  const { data: synthesis } = usePromise<string>(
    async () => {
      if (outputId && selectedItem && isSynthesis) {
        const path = `output/${outputId}/economy/mc-all/grid/${selectedItem.id}`;
        const res = await getStudyData(study.id, path);
        return res;
      }
      return null;
    },
    {
      deps: [study.id, outputId, selectedItem],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleItemTypeChange: ToggleButtonGroupProps["onChange"] = (
    _,
    value: OutputItemType,
  ) => {
    setItemType(value);
  };

  const handleDownload = (matrixData: MatrixType, fileName: string): void => {
    downloadMatrix(matrixData, fileName);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitLayoutView
      left={
        <PropertiesView
          topContent={
            <Box
              sx={{
                width: 1,
                px: 1,
              }}
            >
              <ButtonBack onClick={() => navigate("..")} />
            </Box>
          }
          mainContent={
            <>
              <ToggleButtonGroup
                sx={{ p: 1 }}
                value={itemType}
                exclusive
                size="small"
                orientation="vertical"
                fullWidth
                onChange={handleItemTypeChange}
              >
                <ToggleButton value={OutputItemType.Areas}>
                  {t("study.areas")}
                </ToggleButton>
                <ToggleButton value={OutputItemType.Links}>
                  {t("study.links")}
                </ToggleButton>
                <ToggleButton value={OutputItemType.Synthesis}>
                  {t("study.synthesis")}
                </ToggleButton>
              </ToggleButtonGroup>
              <ListElement
                list={filteredItems}
                currentElement={selectedItemId}
                currentElementKeyToTest="id"
                setSelectedItem={(item) => setSelectedItemId(item.id)}
              />
            </>
          }
          onSearchFilterChange={setSearchValue}
        />
      }
      right={
        isSynthesis ? (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              height: 1,
              width: 1,
              overflow: "auto",
            }}
          >
            <Paper
              sx={{
                p: 2,
                overflow: "auto",
              }}
            >
              <code style={{ whiteSpace: "pre" }}>{synthesis}</code>
            </Paper>
          </Box>
        ) : (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              height: 1,
              width: 1,
              gap: 1,
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                gap: 2,
                flexWrap: "wrap",
              }}
            >
              {(
                [
                  [
                    `${t("study.results.mc")}:`,
                    () => (
                      <>
                        <BooleanFE
                          value={year <= 0}
                          trueText="Synthesis"
                          falseText="Year by year"
                          size="small"
                          variant="outlined"
                          onChange={(event) => {
                            setYear(event?.target.value ? -1 : 1);
                          }}
                        />
                        {year > 0 && (
                          <NumberFE
                            size="small"
                            variant="outlined"
                            value={year}
                            sx={{ m: 0, ml: 1, width: 80 }}
                            inputProps={{
                              min: 1,
                              max: maxYear,
                            }}
                            onChange={(event) => {
                              setYear(Number(event.target.value));
                            }}
                          />
                        )}
                      </>
                    ),
                  ],
                  [
                    `${t("study.results.display")}:`,
                    () => (
                      <SelectFE
                        value={dataType}
                        options={[
                          { value: DataType.General, label: "General values" },
                          { value: DataType.Thermal, label: "Thermal plants" },
                          { value: DataType.Renewable, label: "Ren. clusters" },
                          { value: DataType.Record, label: "RecordYears" },
                          { value: DataType.STStorage, label: "ST Storages" },
                        ]}
                        size="small"
                        variant="outlined"
                        onChange={(event) => {
                          setDataType(event?.target.value as DataType);
                        }}
                      />
                    ),
                  ],
                  [
                    `${t("study.results.temporality")}:`,
                    () => (
                      <SelectFE
                        value={timestep}
                        options={[
                          { value: Timestep.Hourly, label: "Hourly" },
                          { value: Timestep.Daily, label: "Daily" },
                          { value: Timestep.Weekly, label: "Weekly" },
                          { value: Timestep.Monthly, label: "Monthly" },
                          { value: Timestep.Annual, label: "Annual" },
                        ]}
                        size="small"
                        variant="outlined"
                        onChange={(event) => {
                          setTimeStep(event?.target.value as Timestep);
                        }}
                      />
                    ),
                  ],
                ] as const
              ).map(([label, Field]) => (
                <Box
                  key={label}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  <Box component="span" sx={{ opacity: 0.7, mr: 1 }}>
                    {label}
                  </Box>
                  <Field />
                </Box>
              ))}
              <Button
                size="small"
                title={t("global.download")}
                variant="outlined"
                color="primary"
                onClick={() =>
                  matrixRes.data &&
                  handleDownload(matrixRes.data, `matrix_${study.id}`)
                }
                disabled={matrixRes.isLoading}
              >
                <DownloadOutlinedIcon />
              </Button>
            </Box>
            <Box sx={{ flex: 1 }}>
              <UsePromiseCond
                response={mergeResponses(outputRes, matrixRes)}
                ifPending={() => (
                  <Skeleton sx={{ height: 1, transform: "none" }} />
                )}
                ifResolved={([, matrix]) =>
                  matrix && (
                    <EditableMatrix
                      matrix={matrix}
                      matrixTime={false}
                      readOnly
                    />
                  )
                }
                ifRejected={(err) => (
                  <Box
                    sx={{
                      height: 1,
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      flexDirection: "column",
                      gap: 1,
                    }}
                  >
                    {axios.isAxiosError(err) && err.response?.status === 404 ? (
                      <>
                        <GridOffIcon sx={{ fontSize: "80px" }} />
                        {t("study.results.noData")}
                      </>
                    ) : (
                      t("data.error.matrix")
                    )}
                  </Box>
                )}
              />
            </Box>
          </Box>
        )
      }
    />
  );
}

export default ResultDetails;
