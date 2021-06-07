import React, {useEffect, useRef} from "react";

import {makeStyles, PropTypes, Table, TableBody, TableCell, TableHead, TableRow} from "@material-ui/core";
import {MatrixType} from "../../../common/types";

// import jspreadsheet from "jspreadsheet-ce";
//
// export default function MatrixView(props: MatrixType) {
//     const {data, columns, index} = props;
//     const jRef = useRef(null);
//     const options = {
//         data: data,
//         columns: columns.map(title => {
//             return {title: title, width: 100};
//         }),
//     };
//
//     useEffect(() => {
//         if (!jRef.current.jspreadsheet) {
//             jspreadsheet(jRef.current, options);
//         }
//     }, [options]);
//
//     return (
//         <div>
//             <div ref={jRef}/>
//             <br/>
//         </div>
//     );
// }

const useStyles = makeStyles({
  table: {
    minWidth: 650,
  },
});

interface PropsType {
    data: MatrixType;
}

export default function MatrixView(props: PropsType) {
    const {data, columns, index} = props.data;
    const classes = useStyles();

    return (
<Table className={classes.table} size="small" aria-label="a dense table">
        <TableHead>
          <TableRow>
              {columns.map(t => (<TableCell>{t}</TableCell>))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((line, i) => (
            <TableRow key={i}>
                {line.map(t => (<TableCell>{t}</TableCell>))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
}