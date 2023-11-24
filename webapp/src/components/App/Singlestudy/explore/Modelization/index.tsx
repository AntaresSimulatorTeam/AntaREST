import { useMemo } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import TabWrapper from "../TabWrapper";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getAreas, getCurrentAreaId } from "../../../../../redux/selectors";
import useAppDispatch from "../../../../../redux/hooks/useAppDispatch";
import { setCurrentArea } from "../../../../../redux/ducks/studySyntheses";

function Modelization() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const areas = useAppSelector((state) => getAreas(state, study.id));
  const areaId = useAppSelector(getCurrentAreaId);

  const tabList = useMemo(() => {
    const basePath = `/studies/${study.id}/explore/modelization`;

    const handleAreasClick = () => {
      if (areaId.length === 0 && areas.length > 0) {
        const firstAreaId = areas[0].id ?? null;

        if (firstAreaId) {
          dispatch(setCurrentArea(firstAreaId));
          navigate(`${basePath}/area/${firstAreaId}`, { replace: true });
        }
      }
    };

    return [
      {
        label: t("study.modelization.map"),
        path: `${basePath}/map`,
      },
      {
        label: t("study.areas"),
        path: `${basePath}/area/${areaId}`,
        onClick: handleAreasClick,
      },
      {
        label: t("study.links"),
        path: `${basePath}/links`,
      },
      {
        label: t("study.bindingconstraints"),
        path: `${basePath}/bindingcontraint`,
      },
      {
        label: t("study.debug"),
        path: `${basePath}/debug`,
      },
      {
        label: t("study.modelization.tableMode"),
        path: `${basePath}/tablemode`,
      },
    ];
  }, [areaId, areas, dispatch, navigate, study?.id, t]);

  return (
    <Box
      sx={{
        display: "flex",
        flex: 1,
        width: 1,
        overflow: "hidden",
      }}
    >
      <TabWrapper study={study} tabStyle="withoutBorder" tabList={tabList} />
    </Box>
  );
}

export default Modelization;
