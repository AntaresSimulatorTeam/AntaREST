import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { capitalize } from "lodash";
import * as R from "ramda";
import CheckBoxFE from "../../../../../../common/fieldEditors/CheckBoxFE";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { useFormContext } from "../../../../../../common/Form";
import { TSFormFields, SEASONAL_CORRELATION_OPTIONS, TSType } from "../utils";

const borderStyle = "1px solid rgba(255, 255, 255, 0.12)";

function Fields() {
  const { control, getValues, setValue } = useFormContext<TSFormFields>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableContainer>
      <Table sx={{ minWidth: "1050px" }} size="small">
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
          {R.values(TSType)
            .filter((type) => !!getValues(type))
            .map((type) => {
              const isSpecialType =
                type === TSType.Renewables || type === TSType.NTC;
              const emptyDisplay = "-";
              const notApplicableDisplay = "n/a";
              const isReadyMadeStatusEnable = !getValues(
                `${type}.stochasticTsStatus`
              );

              const ifNotSpecialType = (
                fn: (
                  t: Exclude<TSType, TSType.Renewables | TSType.NTC>
                ) => React.ReactNode
              ) => {
                return isSpecialType ? emptyDisplay : fn(type);
              };

              return (
                <TableRow key={type}>
                  <TableCell sx={{ fontWeight: "bold" }}>
                    {capitalize(type)}
                  </TableCell>
                  <TableCell align="center">
                    <SwitchFE
                      value={isReadyMadeStatusEnable}
                      onChange={(_, checked) => {
                        setValue(
                          `${type}.stochasticTsStatus`,
                          !checked as never
                        );
                      }}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <SwitchFE
                      name={`${type}.stochasticTsStatus`}
                      control={control}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <NumberFE
                        name={`${t}.number`}
                        control={control}
                        size="small"
                        fullWidth
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <CheckBoxFE
                        name={`${t}.refresh`}
                        control={control}
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <NumberFE
                        name={`${t}.refreshInterval`}
                        control={control}
                        size="small"
                        fullWidth
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) =>
                      t !== TSType.Thermal ? (
                        <SelectFE
                          name={`${t}.seasonCorrelation`}
                          options={SEASONAL_CORRELATION_OPTIONS}
                          control={control}
                          size="small"
                          disabled={isReadyMadeStatusEnable}
                        />
                      ) : (
                        notApplicableDisplay
                      )
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <CheckBoxFE
                        name={`${t}.storeInInput`}
                        control={control}
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    {ifNotSpecialType((t) => (
                      <CheckBoxFE
                        name={`${t}.storeInOutput`}
                        control={control}
                        disabled={isReadyMadeStatusEnable}
                      />
                    ))}
                  </TableCell>
                  <TableCell align="center">
                    <CheckBoxFE name={`${type}.intraModal`} control={control} />
                  </TableCell>
                  <TableCell align="center">
                    {type !== TSType.NTC ? (
                      <CheckBoxFE
                        name={`${type}.interModal`}
                        control={control}
                      />
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
