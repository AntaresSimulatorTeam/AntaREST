import "jsoneditor";

declare module "jsoneditor" {
  export interface HistoryItem {
    action: string;
    params: object;
    timestamp: Date;
  }

  export default interface JSONEditor {
    /**
     * Only available for mode `code`.
     */
    aceEditor?: AceAjax.Editor;
    /**
     * Expand all fields. Only applicable for mode `tree`, `view`, and `form`.
     */
    expandAll?: VoidFunction;
    /**
     * Only available for mode `tree`, `form`, and `preview`.
     */
    history?: {
      /**
       * Only available for mode `tree`, and `form`.
       */
      history?: HistoryItem[];
      index: number;
      onChange: () => void;
    };
    menu: HTMLDivElement;
  }
}
