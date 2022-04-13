import { useState, useEffect } from "react";
import moment from "moment";
import {
  Paper,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { JobsType, TaskType } from "../../common/types";
import { scrollbarStyle } from "../../theme";

interface PropType {
  content: Array<JobsType>;
}

function JobTableView(props: PropType) {
  const { content } = props;
  const [t] = useTranslation();
  const [sorted, setSorted] = useState<string>();
  const [type, setType] = useState<string>("all");
  const [currentContent, setCurrentContent] = useState<JobsType[]>([]);

  const handleChange = (event: SelectChangeEvent) => {
    setType(event.target.value as string);
  };

  useEffect(() => {
    if (content) {
      if (type !== "all") {
        setCurrentContent(content.filter((o) => o.type === type));
      } else {
        setCurrentContent(content);
      }
    }
  }, [content, type]);

  const filterList = [
    "all",
    TaskType.DOWNLOAD,
    TaskType.LAUNCH,
    TaskType.COPY,
    TaskType.ARCHIVE,
    TaskType.UNARCHIVE,
    TaskType.SCAN,
  ];

  return (
    <Box
      sx={{
        flexGrow: 1,
        mx: 1,
        my: 2,
        overflowX: "hidden",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
      }}
    >
      <FormControl variant="outlined" sx={{ m: 1, mr: 3, minWidth: 160 }}>
        <InputLabel id="jobsView-select-outlined-label">
          {t("jobs:typeFilter")}
        </InputLabel>
        <Select
          labelId="jobsView-select-outlined-label"
          id="jobsView-select-outlined"
          value={type}
          onChange={handleChange}
          label={t("jobs:typeFilter")}
        >
          {filterList.map((item) => (
            <MenuItem value={item} key={item}>
              {t(`jobs:${item}`)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <TableContainer sx={scrollbarStyle} component={Paper}>
        <Table sx={{ width: "100%", height: "90%" }} aria-label="simple table">
          <TableHead>
            <TableRow
              sx={{
                "& td, & th": {
                  borderBottom: "1px solid",
                  borderColor: "divider",
                },
              }}
            >
              <TableCell>{t("main:jobs")}</TableCell>
              <TableCell align="right">{t("singlestudy:type")}</TableCell>
              <TableCell align="right">
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="flex-end"
                >
                  {t("main:date")}
                  {!sorted ? (
                    <ArrowDropUpIcon
                      sx={{
                        cursor: "pointer",
                        color: "action.active",
                        "&:hover": { color: "action.hover" },
                      }}
                      onClick={() => setSorted("date")}
                    />
                  ) : (
                    <ArrowDropDownIcon
                      sx={{
                        cursor: "pointer",
                        color: "action.active",
                        "&:hover": { color: "action.hover" },
                      }}
                      onClick={() => setSorted(undefined)}
                    />
                  )}
                </Box>
              </TableCell>
              <TableCell align="right">{t("jobs:action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentContent
              .sort((a, b) => {
                if (!sorted && sorted !== "date") {
                  return moment(a.date).isAfter(moment(b.date)) ? -1 : 1;
                }
                return moment(a.date).isAfter(moment(b.date)) ? 1 : -1;
              })
              .map((row) => (
                <TableRow
                  key={`${row.name}-name-${row.date}`}
                  sx={{
                    "& td, & th": {
                      borderColor: "divider",
                    },
                    "&:last-child > td, &:last-child > th": {
                      border: 0,
                    },
                  }}
                >
                  <TableCell component="th" scope="row">
                    {row.name}
                  </TableCell>
                  <TableCell align="right">{t(`jobs:${row.type}`)}</TableCell>
                  <TableCell align="right">{row.dateView}</TableCell>
                  <TableCell align="right">{row.action}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default JobTableView;
