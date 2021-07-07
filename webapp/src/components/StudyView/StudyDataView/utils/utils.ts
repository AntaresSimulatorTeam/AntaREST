import { StyleRules, Theme } from "@material-ui/core";

export const writeLeaf = (keys: Array<string>, dataElm: any, value: any, index = 0) => {
  if (index >= keys.length || keys.length === 0) { return; }
  if (!(keys[index] in dataElm)) { return; }
  const key = keys[index];
  if (index === keys.length - 1) {
    // eslint-disable-next-line no-param-reassign
    dataElm[key] = value;
  } else {
    writeLeaf(keys, dataElm[key], value, index + 1);
  }
};

export const CommonStudyStyle = (theme: Theme) : StyleRules<"content" | "root" | "header"> => {
    return {
        root: {
            flex: 1,
            height: '100%',
            display: 'flex',
            flexFlow: 'column nowrap',
            justifyContent: 'flex-start',
            alignItems: 'center',
          },
          header: {
            width: '100%',
            display: 'flex',
            flexFlow: 'row nowrap',
            justifyContent: 'flex-end',
            alignItems: 'center',
          },
          content: {
            padding: theme.spacing(3),
            boxSizing: 'border-box',
            flex: 1,
            width: '100%',
            display: 'flex',
            flexFlow: 'column nowrap',
            justifyContent: 'flex-start',
            alignItems: 'flex-start',
            overflow: 'auto',
          }
    };
}
