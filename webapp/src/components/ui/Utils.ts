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

type ListType = 'Numbered List' | 'Bullet List';

interface AttributesUtils {
  openBalise: string;
  closeBalise: string;
  list?: ListType;
}

interface NodeProcessResult {
  result: string;
  lastListStatus?: ListType;
}

const XmlToHTML = { paragraph: 'div',
  text: 'span',
  symbol: 'span' };

const checkAttributes = (node: XMLElement): AttributesUtils => {
  let openBalise = ''; let
    closeBalise = '';
  let listType: ListType = 'Bullet List';
  let isList = false;
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
        case 'liststyle':
          if (node.attributes[list[i]] === 'Bullet List' || node.attributes[list[i]] === 'Numbered List') { // BOLD
            isList = true;
            listType = node.attributes[list[i]] as ListType;
          }
          break;
        default:
          break;
      }
    }
  }
  return { openBalise, closeBalise, list: isList ? listType : undefined };
};

const nodeProcess = (node: XMLElement, prevListStatus: ListType | undefined, isLastSon = false): NodeProcessResult => {
  const res: NodeProcessResult = { result: '' };
  if (node.type !== undefined) {
    if (node.type === 'element') {
      if (node.name !== undefined) {
        //console.log('ELEMENT NAME: ', node.name);
        let attributesUtils: AttributesUtils = { openBalise: '', closeBalise: '' };
        if (Object.keys(XmlToHTML).includes(node.name)) {
          attributesUtils = checkAttributes(node);

          // List case
          if (attributesUtils.list !== undefined) {
            console.log('LIST ELEMENT: ', node);
            if (prevListStatus === undefined) {
              attributesUtils.openBalise = `${attributesUtils.list === 'Numbered List' ? '<ol><li>' : '<ul><li>'}${attributesUtils.openBalise}`;
            } else if (prevListStatus !== attributesUtils.list) {
              const closePrevBalise = (prevListStatus === 'Numbered List' ? '</ol>' : '</ul>'); // Close previous list
              attributesUtils.openBalise = `${closePrevBalise}${attributesUtils.list === 'Numbered List' ? '<ol><li>' : '<ul><li>'}${attributesUtils.openBalise}`;
            } else {
              attributesUtils.openBalise += `<li>${attributesUtils.openBalise}`;
            }
            attributesUtils.closeBalise += '</li>';
            if (isLastSon) attributesUtils.closeBalise += (attributesUtils.list === 'Numbered List' ? '</ol>' : '</ul>');
          } else if (prevListStatus !== undefined) {
            //console.log('NOT LIST ELEMENT / PREVIOUS LIST');
            const closePrevBalise = (prevListStatus === 'Numbered List' ? '</ol>' : '</ul>'); // Close previous list
            attributesUtils.openBalise = `${closePrevBalise}<${(XmlToHTML as any)[node.name]}>${attributesUtils.openBalise}`;
            attributesUtils.closeBalise += `</${(XmlToHTML as any)[node.name]}>`;
          } else {
            //console.log('NOT LIST ELEMENT');
            attributesUtils.openBalise = `<${(XmlToHTML as any)[node.name]}>${attributesUtils.openBalise}`;
            attributesUtils.closeBalise += `</${(XmlToHTML as any)[node.name]}>`;
          }
        }

        if (node.elements !== undefined && node.elements.length > 0) {
          let completeResult: NodeProcessResult = { result: '' };
          for (let j = 0; j < node.elements.length; j++) {
            completeResult = nodeProcess(node.elements[j], completeResult.lastListStatus, j === node.elements.length - 1);
            res.result += completeResult.result;
          }
          return { result: attributesUtils.openBalise + res.result + attributesUtils.closeBalise, lastListStatus: attributesUtils.list };
        }
      }
    } else if (node.type === 'text') {
      if (node.text !== undefined) return { result: (node.text as string) };
    }
  } else if (node.elements !== undefined) {
    let completeResult: NodeProcessResult = { result: '' };
    for (let i = 0; i < node.elements.length; i++) {
      completeResult = nodeProcess(node.elements[i], completeResult.lastListStatus, i === node.elements.length - 1);
      res.result += completeResult.result;
    }
  }

  return res;
};

export const convertXMLToHTML = (data: string) => {
  const xmlStr = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(xmlStr);
  return nodeProcess(xmlElement, undefined, true).result;
};

export const convertHTMLToXML = (data: string) => {
  const htmlStr = xml2json(data, { compact: false, spaces: 4 });
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

PARAMS:
textcolor
fontweight
fontpointsize
fontfamily
fontstyle
fontunderline
fontface
alignment
parspacingafter
parspacingbefore
linespacing
margin-left
margin-right
margin-top
margin-bottom
leftindent
leftsubindent
*/

export default {};
