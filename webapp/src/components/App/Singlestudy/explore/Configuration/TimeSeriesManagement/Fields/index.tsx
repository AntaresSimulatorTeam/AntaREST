import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from "@mui/material";
import { StudyMetadata } from "../../../../../../../common/types";
import CheckBoxFE from "../../../../../../common/fieldEditors/CheckBoxFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { useFormContext } from "../../../../../../common/Form";
import {
  FormValues,
  SEASONAL_CORRELATION_OPTIONS,
  TimeSeriesType,
} from "../utils";

const borderStyle = "1px solid rgba(255, 255, 255, 0.12)";

interface Props {
  study: StudyMetadata;
}

function Fields(props: Props) {
  const { register } = useFormContext<FormValues>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableContainer>
      <Table sx={{ minWidth: "1050px" }}>
        <TableHead>
          <TableRow sx={{ th: { py: 1, borderBottom: "none" } }}>
            <TableCell />
            <TableCell sx={{ borderRight: borderStyle }} align="center">
              Ready made TS
            </TableCell>
            <TableCell
              sx={{ borderRight: borderStyle }}
              align="center"
              colSpan={7}
            >
              Stochastic TS
            </TableCell>
            <TableCell align="center" colSpan={2}>
              Draw correlation
            </TableCell>
          </TableRow>
          <TableRow
            sx={{
              th: {
                fontWeight: "bold",
                borderBottom: borderStyle,
              },
            }}
          >
            <TableCell />
            <TableCell align="center">Status</TableCell>
            <TableCell align="center">Status</TableCell>
            <TableCell align="center">Number</TableCell>
            <TableCell align="center">Refresh</TableCell>
            <TableCell align="center">Refresh interval</TableCell>
            <TableCell align="center">Season correlation</TableCell>
            <TableCell align="center">Store in input</TableCell>
            <TableCell align="center">Store in output</TableCell>
            <TableCell align="center">Intra-modal</TableCell>
            <TableCell align="center">inter-modal</TableCell>
          </TableRow>
        </TableHead>
        <TableBody
          sx={{
            "th, td": { borderBottom: borderStyle },
          }}
        >
          {(
            Object.keys(TimeSeriesType) as Array<keyof typeof TimeSeriesType>
          ).map((row) => {
            const type = TimeSeriesType[row];
            const isSpecialType =
              type === TimeSeriesType.Renewables || type === TimeSeriesType.NTC;
            const emptyDisplay = "-";

            const render = (node: React.ReactNode) => {
              return isSpecialType ? emptyDisplay : node;
            };

            return (
              <TableRow key={row}>
                <TableCell sx={{ fontWeight: "bold" }}>{row}</TableCell>
                <TableCell align="center">
                  <SwitchFE {...register(`${type}.readyMadeTsStatus`)} />
                </TableCell>
                <TableCell align="center">
                  {render(
                    <SwitchFE {...register(`${type}.stochasticTsStatus`)} />
                  )}
                </TableCell>
                <TableCell align="center">
                  {render(
                    <TextField
                      type="number"
                      {...register(`${type}.number`, {
                        valueAsNumber: true,
                      })}
                    />
                  )}
                </TableCell>
                <TableCell align="center">
                  {render(<CheckBoxFE {...register(`${type}.refresh`)} />)}
                </TableCell>
                <TableCell align="center">
                  {render(
                    <TextField
                      type="number"
                      {...register(`${type}.refreshInterval`, {
                        valueAsNumber: true,
                      })}
                    />
                  )}
                </TableCell>
                <TableCell align="center">
                  {render(
                    type !== TimeSeriesType.Thermal ? (
                      <SelectFE
                        options={SEASONAL_CORRELATION_OPTIONS}
                        {...register(`${type}.seasonCorrelation`)}
                      />
                    ) : (
                      "n/a"
                    )
                  )}
                </TableCell>
                <TableCell align="center">
                  {render(<CheckBoxFE {...register(`${type}.storeInInput`)} />)}
                </TableCell>
                <TableCell align="center">
                  {render(
                    <CheckBoxFE {...register(`${type}.storeInOutput`)} />
                  )}
                </TableCell>
                <TableCell align="center">
                  <CheckBoxFE {...register(`${type}.intraModal`)} />
                </TableCell>
                <TableCell align="center">
                  {type !== TimeSeriesType.NTC ? (
                    <CheckBoxFE {...register(`${type}.interModal`)} />
                  ) : (
                    emptyDisplay
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default Fields;
