import ScheduleOutlinedIcon from "@mui/icons-material/ScheduleOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import AltRouteOutlinedIcon from "@mui/icons-material/AltRouteOutlined";
import SecurityOutlinedIcon from "@mui/icons-material/SecurityOutlined";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import { Box, Divider, Tooltip, Typography, styled } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import {
  buildModificationDate,
  convertUTCToLocalTime,
  countAllChildrens,
  displayVersionName,
} from "../../../../services/utils";
import { StudyMetadata, VariantTree } from "../../../../common/types";
import { PUBLIC_MODE_LIST } from "../../../common/utils/constants";

const MAX_STUDY_TITLE_LENGTH = 45;

const TinyText = styled(Typography)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.text.secondary,
}));

const LinkText = styled(Link)(({ theme }) => ({
  fontSize: "14px",
  color: theme.palette.secondary.main,
}));

const StyledDivider = styled(Divider)(({ theme }) => ({
  margin: theme.spacing(0, 1),
  width: "1px",
  height: "20px",
  backgroundColor: theme.palette.divider,
}));

const BoxContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  justifyContent: "flex-start",
  alignItems: "center",
  margin: theme.spacing(0, 3),
}));

interface Props {
  study: StudyMetadata | undefined;
  parent: StudyMetadata | undefined;
  childrenTree: VariantTree | undefined;
}

function NavHeaderInfo({ study, parent, childrenTree }: Props) {
  const [t, i18n] = useTranslation();
  const publicModeLabel =
    PUBLIC_MODE_LIST.find((mode) => mode.id === study?.publicMode)?.name || "";

  if (!study) {
    return null;
  }

  return (
    <BoxContainer
      sx={{
        my: 1,
        width: 1,
        boxSizing: "border-box",
      }}
    >
      <BoxContainer sx={{ ml: 0 }}>
        <ScheduleOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>{convertUTCToLocalTime(study.creationDate)}</TinyText>
      </BoxContainer>
      <BoxContainer>
        <UpdateOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>
          {buildModificationDate(study.modificationDate, t, i18n.language)}
        </TinyText>
      </BoxContainer>
      <StyledDivider />
      <BoxContainer>
        <TinyText>{`v${displayVersionName(study.version)}`}</TinyText>
      </BoxContainer>
      {parent && (
        <BoxContainer>
          <AltRouteOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <Tooltip title={parent.name}>
            <LinkText to={`/studies/${parent.id}`}>
              {`${parent.name.substring(0, MAX_STUDY_TITLE_LENGTH)}...`}
            </LinkText>
          </Tooltip>
        </BoxContainer>
      )}
      {childrenTree && (
        <BoxContainer>
          <AccountTreeOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
          <TinyText>{countAllChildrens(childrenTree)}</TinyText>
        </BoxContainer>
      )}
      <StyledDivider />
      <BoxContainer>
        <PersonOutlineOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>{study?.owner.name}</TinyText>
      </BoxContainer>
      <BoxContainer>
        <SecurityOutlinedIcon sx={{ color: "text.secondary", mr: 1 }} />
        <TinyText>{t(publicModeLabel)}</TinyText>
      </BoxContainer>
    </BoxContainer>
  );
}

export default NavHeaderInfo;
