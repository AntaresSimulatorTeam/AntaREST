import lodash from 'lodash';

export const UNLOADED_MARKER = '.unloaded';

export const markUnloaded = (node: any): any => {
  const markedNode = { ...node };
  Object.keys(node).forEach((key) => {
    const nodeitem = node[key];
    if (typeof nodeitem === 'object' && Object.keys(nodeitem).length === 0) {
      markedNode[key] = { [UNLOADED_MARKER]: true };
    } else {
      markedNode[key] = nodeitem;
    }
  });
  return markedNode;
};

export const isUnloaded = (node: any): boolean => Object.keys(node).indexOf(UNLOADED_MARKER) !== -1;

export const updateData = (datajson: any, path: string, itemdata: any): any => {
  const pathitems = lodash.trim(path.trim(), '/').split('/');
  const updatedData = { ...datajson };
  let target: any = {};
  let src: any = updatedData;
  const targetData: any = target;
  for (let index = 0; index < pathitems.length; index += 1) {
    const element = pathitems[index];
    target[element] = {};
    src = src[element];
    if (index === pathitems.length - 1) {
      target[element] = markUnloaded(itemdata);
      delete src[UNLOADED_MARKER];
    } else {
      target = target[element];
    }
  }
  return lodash.merge(updatedData, targetData);
};
