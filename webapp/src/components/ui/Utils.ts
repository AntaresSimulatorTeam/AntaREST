import Draft, { ContentState, convertFromHTML, convertToRaw, DraftBlockRenderMap, EditorState } from 'draft-js';
import draftToHtml from 'draftjs-to-html';
import * as Immutable from 'immutable';
import { Element as XMLElement, xml2json } from 'xml-js';

export const defaultBlockRenderMap = (): DraftBlockRenderMap => {
  const blockRenderMap = Immutable.Map({
    ins: {
      element: 'u',
    },
  });
  return Draft.DefaultDraftBlockRenderMap.merge(blockRenderMap);
};

export const htmlToDraftJs = (data: string, extendedBlockRenderMap?: DraftBlockRenderMap): ContentState => {
  const blocksFromHTML = convertFromHTML(data, undefined, extendedBlockRenderMap);
  return ContentState.createFromBlockArray(
    blocksFromHTML.contentBlocks,
    blocksFromHTML.entityMap,
  );
};

interface BlockMap {
  from: string;
  to: string;
}

const blockMap: Array<BlockMap> = [{ from: 'ins', to: 'u' },
  { from: 'em', to: 'i' },
  { from: 'strong', to: 'b' }];

const replaceAll = (string: string, search: string, replace: string): string => string.split(search).join(replace);

const toDraftJsHtml = (data: string): string => {
  let tmp = data;
  blockMap.forEach((elm) => {
    tmp = replaceAll(tmp, `<${elm.from}>`, `<${elm.to}>`);
    tmp = replaceAll(tmp, `</${elm.from}>`, `</${elm.to}>`);
  });
  return tmp;
};

export const DraftJsToHtml = (editorState: EditorState): string => {
  console.log('STATE: ', editorState.getCurrentContent());
  const rawContentState = convertToRaw(editorState.getCurrentContent());
  console.log('RAW: ', rawContentState);
  return toDraftJsHtml(draftToHtml(
    rawContentState,
  ));
};

export const xmlToJson = (data: string): string => xml2json(data, { compact: false, spaces: 4 });

const xmlToRaw = (data: string) => {
  const xmlStr = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(xmlStr);
  console.log('OUI OUI: ', xmlStr);
  const result = '';
};

const nodeProcess = (node: XMLElement): string => {
  let res = '';
  if (node.type !== undefined) {
    console.log('TITLE');
    if(node.type === 'element') {
      
    } else if (node.type === 'text') {
      
    }
  } else if (node.elements !== undefined) {
    for (let i = 0; i < node.elements.length; i++) {
      res += nodeProcess(node.elements[i]);
    }
  }

  return res;
};

/*
NOTE:
<paragraph> => p
<text> => <p>
<symbol> => \tab
blocks: Array<RawDraftContentBlock>;
entityMap: { [key: string]: RawDraftEntity };

elements: {
  type: 'element' | 'text
  attributes: {}
  name?: 'NAME OF ELEMENT' or text?: ''
  elements
}
*/

export default {};
