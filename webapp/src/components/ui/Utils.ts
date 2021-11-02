/* eslint-disable no-plusplus */
import { ContentState, convertFromHTML, convertToRaw, EditorState } from 'draft-js';
import draftToHtml from 'draftjs-to-html';
import { Element as XMLElement, js2xml, xml2json } from 'xml-js';

interface BlockMap {
  from: string;
  to: string;
}

const blockMap: Array<BlockMap> = [{ from: 'ins', to: 'u' },
  { from: 'em', to: 'i' },
  { from: 'strong', to: 'b' }];

const XmlToHTML = { paragraph: 'p',
  text: 'span',
  symbol: 'span' };

type ListType = 'Numbered List' | 'Bullet List';

interface AttributesUtils {
  openBalise: string;
  closeBalise: string;
  list?: ListType;
}

interface NodeProcessResult {
  result: string;
  listSeq?: ListType;
}

const replaceAll = (string: string, search: string, replace: string): string => string.split(search).join(replace);

const toDraftJsHtml = (data: string): string => {
  let tmp = data;
  blockMap.forEach((elm) => {
    tmp = replaceAll(tmp, `<${elm.from}>`, `<${elm.to}>`);
    tmp = replaceAll(tmp, `</${elm.from}>`, `</${elm.to}>`);
  });
  return tmp;
};

/*
------------------------------------------------------
CONVERT CUSTOM ANTARES XML TO DRAFT JS INTERNAL MODEL
------------------------------------------------------
*/

const parseXMLAttributes = (node: XMLElement): AttributesUtils => {
  let openBalise = ''; let
    closeBalise = '';
  let listType: ListType = 'Bullet List';
  let isList = false;
  if (node.attributes !== undefined) {
    const list = Object.keys(node.attributes);
    for (let i = 0; i < list.length; i++) {
      switch (list[i]) {
        case 'fontweight':
          if (parseInt(node.attributes[list[i]] as string, 10) > 0) { // BOLD
            openBalise += '<b>';
            closeBalise = `</b>${closeBalise}`;
          }
          break;
        case 'fontunderline':
          openBalise += '<u>';
          closeBalise = `</u>${closeBalise}`;
          break;
        case 'fontstyle':
          if (parseInt(node.attributes[list[i]] as string, 10) > 0) { // BOLD
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

const parseXMLToHTMLNode = (node: XMLElement, prevListSeq: ListType | undefined, isLastSon = false): NodeProcessResult => {
  const res: NodeProcessResult = { result: '' };
  if (node.type !== undefined) {
    if (node.type === 'element') {
      if (node.name !== undefined) {
        let attributesUtils: AttributesUtils = { openBalise: '', closeBalise: '' };
        if (Object.keys(XmlToHTML).includes(node.name)) {
          attributesUtils = parseXMLAttributes(node);

          if (attributesUtils.list !== undefined) {
            if (prevListSeq === undefined) {
              attributesUtils.openBalise = `${attributesUtils.list === 'Numbered List' ? '<ol><li>' : '<ul><li>'}${attributesUtils.openBalise}`;
            } else if (prevListSeq !== attributesUtils.list) {
              const closePrevBalise = (prevListSeq === 'Numbered List' ? '</ol>' : '</ul>'); // Close previous list
              attributesUtils.openBalise = `${closePrevBalise}${attributesUtils.list === 'Numbered List' ? '<ol><li>' : '<ul><li>'}${attributesUtils.openBalise}`;
            } else {
              attributesUtils.openBalise = `<li>${attributesUtils.openBalise}`;
            }
            attributesUtils.closeBalise += '</li>';
            if (isLastSon) attributesUtils.closeBalise += (attributesUtils.list === 'Numbered List' ? '</ol>' : '</ul>');
          } else if (prevListSeq !== undefined) {
            const closePrevBalise = (prevListSeq === 'Numbered List' ? '</ol>' : '</ul>'); // Close previous list
            attributesUtils.openBalise = `${closePrevBalise}<${(XmlToHTML as any)[node.name]}>${attributesUtils.openBalise}`;
            attributesUtils.closeBalise += `</${(XmlToHTML as any)[node.name]}>`;
          } else {
            attributesUtils.openBalise = `<${(XmlToHTML as any)[node.name]}>${attributesUtils.openBalise}`;
            attributesUtils.closeBalise += `</${(XmlToHTML as any)[node.name]}>`;
          }
        }

        if (node.elements !== undefined && node.elements.length > 0) {
          let completeResult: NodeProcessResult = { result: '' };
          for (let j = 0; j < node.elements.length; j++) {
            completeResult = parseXMLToHTMLNode(node.elements[j], completeResult.listSeq, j === node.elements.length - 1);
            res.result += completeResult.result;
          }
          return { result: attributesUtils.openBalise + res.result + attributesUtils.closeBalise, listSeq: attributesUtils.list };
        }
      }
    } else if (node.type === 'text') {
      if (node.text !== undefined) return { result: (node.text as string) };
    }
  } else if (node.elements !== undefined) {
    let completeResult: NodeProcessResult = { result: '' };
    for (let i = 0; i < node.elements.length; i++) {
      completeResult = parseXMLToHTMLNode(node.elements[i], completeResult.listSeq, i === node.elements.length - 1);
      res.result += completeResult.result;
    }
  }

  return res;
};

const convertXMLToHTML = (data: string): string => {
  const xmlStr = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(xmlStr);
  return parseXMLToHTMLNode(xmlElement, undefined, true).result;
};

export const convertXMLToDraftJS = (data: string): ContentState => {
  const htmlData = convertXMLToHTML(data);
  console.log('XML TO HTML: ', htmlData);
  const blocks = convertFromHTML(htmlData, undefined);
  return ContentState.createFromBlockArray(
    blocks.contentBlocks,
    blocks.entityMap,
  );
};

/*
------------------------------------------------------
CONVERT DRAFT JS INTERNAL MODEL TO CUSTOM ANTARES XML
------------------------------------------------------
*/

const HTMLToAttributes = {
  b: { fontweight: '700' },
  i: { fontstyle: '93' },
  u: { fontunderline: '1' },
};

const parseHTMLToXMLNode = (node: XMLElement, parent: XMLElement, lastListSeq = 0): number => {
  let listSeq = 0;

  const parseSon = (nodeElement: XMLElement): void => {
    if (nodeElement.elements !== undefined) {
      let prevListSeq = 0;
      for (let i = 0; i < nodeElement.elements.length; i++) {
        prevListSeq = parseHTMLToXMLNode(nodeElement.elements[i], nodeElement, prevListSeq);
      }
    }
  };

  if (node.type !== undefined) {
    if (node.type === 'element') {
      if (node.name !== undefined) {
        switch (node.name) {
          case 'p':
            // eslint-disable-next-line no-param-reassign
            node.name = 'paragraph';
            parseSon(node);
            break;

          case 'b':
          case 'i':
          case 'u':
            if (parent !== node) {
              if ((parent.name === 'paragraph' || parent.name === 'text') && parent.elements !== undefined && parent.elements.length === 1) {
                // eslint-disable-next-line no-param-reassign
                parent.attributes = { ...parent.attributes, ...(HTMLToAttributes as any)[node.name] };
                // eslint-disable-next-line no-param-reassign
                parent.elements = node.elements;
                parseSon(parent);
              } else {
                // eslint-disable-next-line no-param-reassign
                node.attributes = { ...node.attributes, ...(HTMLToAttributes as any)[node.name] };
                // eslint-disable-next-line no-param-reassign
                node.name = 'symbol';
                parseSon(node);
              }
            }
            break;

          case 'span':
            // eslint-disable-next-line no-param-reassign
            node.name = 'text';
            parseSon(node);
            break;

          case 'li':
            if (parent !== node && parent.name !== undefined && (parent.name === 'ol' || parent.name === 'ul')) {
              listSeq = (lastListSeq + 1);
              // eslint-disable-next-line no-param-reassign
              node.attributes = { ...node.attributes,
                alignment: '1',
                leftindent: '60',
                leftsubindent: '60',
                bulletstyle: '512',
                bulletname: 'standard/circle',
                bulletnumber: listSeq.toString(),
                liststyle: parent.name === 'ol' ? 'Numbered List' : 'Bullet List' };
              // eslint-disable-next-line no-param-reassign
              node.name = 'paragraph';
              parseSon(node);
            }
            break;

          case 'ul':
          case 'ol':
            parseSon(node);
            // eslint-disable-next-line no-param-reassign
            node.name = 'paragraph';
            break;

          default:
            parseSon(node);
            break;
        }
      }
    }
  } else if (node.elements !== undefined) {
    parseSon(node);
  }
  return listSeq;
};

const convertHTMLToXML = (data: string): string => {
  const htmlStr: string = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(htmlStr);
  console.log('HTML TO XML: ', data);
  parseHTMLToXMLNode(xmlElement, xmlElement);
  const res = js2xml(xmlElement, { compact: false, spaces: 4 });
  console.log('HTML TO XML RESULT: ', res);
  return res;
};

const addXMLHeader = (xmlData: string): string => {
  let res = '<?xml version="1.0" encoding="UTF-8"?>';
  res += '<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">';
  res += '<paragraphlayout textcolor="#000000" fontpointsize="9" fontfamily="70" fontstyle="90" fontweight="400" fontunderlined="0" fontface="Segoe UI" alignment="1" parspacingafter="10" parspacingbefore="0" linespacing="10">';
  res += xmlData;
  res += '</paragraphlayout>';
  res += '</richtext>';
  return res;
};

export const convertDraftJSToXML = (editorState: EditorState): string => {
  const rawContentState = convertToRaw(editorState.getCurrentContent());
  const htmlElement = toDraftJsHtml(draftToHtml(
    rawContentState,
  ));
  let htmlToXml = addXMLHeader(htmlElement);
  htmlToXml = convertHTMLToXML(htmlToXml);
  return htmlToXml;
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
