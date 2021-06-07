import {useEffect, useRef} from "react";
import jspreadsheet from "jspreadsheet-ce";

import "../node_modules/jspreadsheet-ce/dist/jspreadsheet.css";
import {PropTypes} from "@material-ui/core";
import {MatrixType} from "../../../common/types";

export default function MatrixView(props: MatrixType) {
    const {data, columns, index} = props;
    const jRef = useRef(null);
    const options = {
        data: data,
        columns: columns.map(title => {
            return {title: title, width: 100};
        }),
    };

    useEffect(() => {
        if (!jRef.current.jspreadsheet) {
            jspreadsheet(jRef.current, options);
        }
    }, [options]);

    return (
        <div>
            <div ref={jRef}/>
            <br/>
        </div>
    );
}