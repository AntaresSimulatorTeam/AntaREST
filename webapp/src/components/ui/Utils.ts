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
  console.log('ARRAY: ', editorState.getCurrentContent().getBlocksAsArray());
  return toDraftJsHtml(draftToHtml(
    rawContentState,
  ));
};

export const xmlToJson = (data: string): string => xml2json(data, { compact: false, spaces: 4 });

interface Balise {
  openBalise: string;
  closeBalise: string;
}

const XmlToHTML = { paragraph: 'div',
  text: 'span',
  symbol: 'li' };

const checkAttributes = (node: XMLElement): Balise => {
  let openBalise = ''; let
    closeBalise = '';
  if (node.attributes !== undefined) {
    const list = Object.keys(node.attributes);
    for (let i = 0; i < list.length; i++) {
      switch (list[i]) {
        case 'fontweight':
          if (node.attributes[list[i]] === '700') { // BOLD
            openBalise += '<b>';
            closeBalise = `</b>${closeBalise}`;
          }
          break;
        case 'fontunderline':
          openBalise += '<u>';
          closeBalise = `</u>${closeBalise}`;
          break;
        case 'fontstyle':
          if (node.attributes[list[i]] === '93') { // BOLD
            openBalise += '<i>';
            closeBalise = `</i>${closeBalise}`;
          }
          break;

        default:
          break;
      }
    }
  }
  return { openBalise, closeBalise };
};

const nodeProcess = (node: XMLElement): string => {
  let res = '';
  if (node.type !== undefined) {
    if (node.type === 'element') {
      if (node.name !== undefined) {
        let balises: Balise = { openBalise: '', closeBalise: '' };
        switch (node.name) {
          case 'paragraph':
          case 'text':
            balises = checkAttributes(node);
            balises.openBalise = `<${XmlToHTML[node.name]}>${balises.openBalise}`;
            balises.closeBalise += `</${XmlToHTML[node.name]}>`;
            break;
          case 'symbol':
            balises = checkAttributes(node);
            balises.openBalise = `<${XmlToHTML[node.name]}>&ensp;`;
            balises.closeBalise += `</${XmlToHTML[node.name]}>`;
            break;
          default:
            break;
        }

        if (node.elements !== undefined && node.elements.length > 0) {
          for (let j = 0; j < node.elements.length; j++) {
            res += nodeProcess(node.elements[j]);
          }
          return balises.openBalise + res + balises.closeBalise;
        }
      }
    } else if (node.type === 'text') {
      if (node.text !== undefined) return (node.text as string);
    }
  } else if (node.elements !== undefined) {
    for (let i = 0; i < node.elements.length; i++) {
      res += nodeProcess(node.elements[i]);
    }
  }

  return res;
};

export const convertXMLToHTML = (data: string) => {
  const xmlStr = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(xmlStr);
  return nodeProcess(xmlElement);
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
