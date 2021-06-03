import React, {useEffect, useRef} from "react";
import {MatrixType} from "../../../../common/types";
import jspreadsheet from "jspreadsheet-ce";
 import "../../../../../node_modules/jspreadsheet-ce/dist/jexcel.css";

 interface PropTypes {
   data: MatrixType;
 }

 export default function MatrixView(props: PropTypes) {
     const {data, columns} = props.data;
     const jRef = useRef(null);

     const options = {
         data: !!data ? data: [],
         columns: !!columns ? columns.map(title => {
             return {title: title, width: 100};
         }) : [],
     };

     useEffect(() => {
        if(jRef === null)
          return ;

        const current = jRef.current;
        if(current === null)
          return ;

         if (!(current as any).jspreadsheet) {
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