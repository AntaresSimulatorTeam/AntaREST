export const writeLeaf = (
  keys: Array<string>,
  dataElm: never,
  value: never,
  index = 0
): void => {
  if (index >= keys.length || keys.length === 0) {
    return;
  }
  if (!(keys[index] in dataElm)) {
    return;
  }
  const key = keys[index];
  if (index === keys.length - 1) {
    // eslint-disable-next-line no-param-reassign
    dataElm[key] = value;
  } else {
    writeLeaf(keys, dataElm[key], value, index + 1);
  }
};

export default {};
