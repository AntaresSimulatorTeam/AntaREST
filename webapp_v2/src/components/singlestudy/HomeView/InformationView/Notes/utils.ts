/* eslint-disable no-param-reassign */
/* eslint-disable no-plusplus */
import { ContentState, convertToRaw, EditorState } from "draft-js";
import draftToHtml from "draftjs-to-html";
import { convertFromHTML } from "draft-convert";
import { Element as XMLElement, js2xml, xml2json } from "xml-js";

interface BlockMap {
  from: string;
  to: string;
}

const blockMap: Array<BlockMap> = [
  { from: "ins", to: "u" },
  { from: "em", to: "i" },
  { from: "strong", to: "b" },
];

const XmlToHTML = { paragraph: "p", text: "span" };

type ListType = "Numbered List" | "Bullet List";

interface AttributesUtils {
  openBalise: string;
  closeBalise: string;
  list?: ListType;
}

interface NodeProcessResult {
  result: string;
  listSeq?: ListType;
}

const replaceAll = (string: string, search: string, replace: string): string =>
  string.split(search).join(replace);

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
  let openBalise = "";
  let closeBalise = "";
  let listType: ListType = "Bullet List";
  let isList = false;
  if (node.attributes !== undefined) {
    const list = Object.keys(node.attributes);
    for (let i = 0; i < list.length; i++) {
      switch (list[i]) {
        case "fontweight":
          if (parseInt(node.attributes[list[i]] as string, 10) > 0) {
            // BOLD
            openBalise += "<b>";
            closeBalise = `</b>${closeBalise}`;
          }
          break;
        case "fontunderlined":
          openBalise += "<u>";
          closeBalise = `</u>${closeBalise}`;
          break;
        case "fontstyle":
          if (parseInt(node.attributes[list[i]] as string, 10) > 0) {
            // BOLD
            openBalise += "<i>";
            closeBalise = `</i>${closeBalise}`;
          }
          break;
        case "liststyle":
          if (
            node.attributes[list[i]] === "Bullet List" ||
            node.attributes[list[i]] === "Numbered List"
          ) {
            // BOLD
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

const parseXMLToHTMLNode = (
  node: XMLElement,
  parent: XMLElement,
  prevListSeq: ListType | undefined,
  isLastSon = false
): NodeProcessResult => {
  const res: NodeProcessResult = { result: "" };
  if (node.type !== undefined) {
    if (node.type === "element") {
      if (node.name !== undefined) {
        let attributesUtils: AttributesUtils = {
          openBalise: "",
          closeBalise: "",
        };
        if (node.name === "symbol") {
          if (
            node.elements !== undefined &&
            node.elements.length === 1 &&
            node.elements[0].type === "text" &&
            node.elements[0].text !== undefined
          ) {
            if (node.elements[0].text === "9") {
              return { result: "&nbsp;" };
            }
            if (node.elements[0].text === "34") {
              return { result: '"' };
            }
          }
        } else if (Object.keys(XmlToHTML).includes(node.name)) {
          attributesUtils = parseXMLAttributes(node);

          if (attributesUtils.list !== undefined) {
            if (prevListSeq === undefined) {
              attributesUtils.openBalise = `${
                attributesUtils.list === "Numbered List"
                  ? "<ol><li>"
                  : "<ul><li>"
              }${attributesUtils.openBalise}`;
            } else if (prevListSeq !== attributesUtils.list) {
              const closePrevBalise =
                prevListSeq === "Numbered List" ? "</ol>" : "</ul>"; // Close previous list
              attributesUtils.openBalise = `${closePrevBalise}${
                attributesUtils.list === "Numbered List"
                  ? "<ol><li>"
                  : "<ul><li>"
              }${attributesUtils.openBalise}`;
            } else {
              attributesUtils.openBalise = `<li>${attributesUtils.openBalise}`;
            }
            attributesUtils.closeBalise += "</li>";
            if (isLastSon)
              attributesUtils.closeBalise +=
                attributesUtils.list === "Numbered List" ? "</ol>" : "</ul>";
          } else if (prevListSeq !== undefined) {
            const closePrevBalise =
              prevListSeq === "Numbered List" ? "</ol>" : "</ul>"; // Close previous list
            attributesUtils.openBalise = `${closePrevBalise}<${
              (XmlToHTML as any)[node.name]
            }>${attributesUtils.openBalise}`;
            attributesUtils.closeBalise += `</${
              (XmlToHTML as any)[node.name]
            }>`;
          } else {
            attributesUtils.openBalise = `<${(XmlToHTML as any)[node.name]}>${
              attributesUtils.openBalise
            }`;
            attributesUtils.closeBalise += `</${
              (XmlToHTML as any)[node.name]
            }>`;
          }
        }

        if (node.elements !== undefined && node.elements.length > 0) {
          let completeResult: NodeProcessResult = { result: "" };
          for (let j = 0; j < node.elements.length; j++) {
            completeResult = parseXMLToHTMLNode(
              node.elements[j],
              node,
              completeResult.listSeq,
              j === node.elements.length - 1
            );
            res.result += completeResult.result;
          }
          return {
            result:
              attributesUtils.openBalise +
              res.result +
              attributesUtils.closeBalise,
            listSeq: attributesUtils.list,
          };
        }
      }
    } else if (node.type === "text") {
      if (node.text !== undefined)
        return { result: replaceAll(node.text as string, '"', "") };
    }
  } else if (node.elements !== undefined) {
    let completeResult: NodeProcessResult = { result: "" };
    for (let i = 0; i < node.elements.length; i++) {
      completeResult = parseXMLToHTMLNode(
        node.elements[i],
        node,
        completeResult.listSeq,
        i === node.elements.length - 1
      );
      res.result += completeResult.result;
    }
  }

  return res;
};

const convertXMLToHTML = (data: string): string => {
  const xmlStr = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(xmlStr);
  return parseXMLToHTMLNode(xmlElement, xmlElement, undefined, true).result;
};

export const convertXMLToDraftJS = (data: string): ContentState => {
  const htmlData = convertXMLToHTML(data);
  return convertFromHTML(htmlData);
};

/*
------------------------------------------------------
CONVERT DRAFT JS INTERNAL MODEL TO CUSTOM ANTARES XML
------------------------------------------------------
*/

const HTMLToAttributes = {
  b: { fontweight: "92" },
  i: { fontstyle: "93" },
  u: { fontunderlined: "1" },
};

enum ParseHTMLToXMLNodeActions {
  DELETE = "DELETE",
  COPYCHILD = "COPYCHILD",
  TEXTTOELEMENTS = "TEXTTOELEMENTS",
  NONE = "NONE",
}

interface ParseHTMLToXMLActionList {
  action: ParseHTMLToXMLNodeActions;
  node: XMLElement;
}

const parseHTMLToXMLNode = (
  node: XMLElement,
  parent: XMLElement,
  lastListSeq = 0
): ParseHTMLToXMLNodeActions => {
  let action: ParseHTMLToXMLNodeActions = ParseHTMLToXMLNodeActions.NONE;
  const parseChild = (nodeElement: XMLElement): ParseHTMLToXMLNodeActions => {
    let resultAction: ParseHTMLToXMLNodeActions =
      ParseHTMLToXMLNodeActions.NONE;
    if (nodeElement.elements !== undefined) {
      const actionList: Array<ParseHTMLToXMLActionList> = [];
      let childAction: ParseHTMLToXMLNodeActions =
        ParseHTMLToXMLNodeActions.NONE;
      for (let i = 0; i < nodeElement.elements.length; i++) {
        childAction = parseHTMLToXMLNode(
          nodeElement.elements[i],
          nodeElement,
          i
        );
        if (childAction !== ParseHTMLToXMLNodeActions.NONE) {
          actionList.push({
            action: childAction,
            node: nodeElement.elements[i],
          });
        }
      }
      actionList.forEach((elm: ParseHTMLToXMLActionList) => {
        if (nodeElement.elements !== undefined) {
          if (elm.action === ParseHTMLToXMLNodeActions.DELETE) {
            nodeElement.elements = nodeElement.elements.filter(
              (item) => item !== elm.node
            );
          } else if (
            elm.node.elements !== undefined &&
            elm.node.elements.length > 0
          ) {
            let newElements: Array<XMLElement> = [];
            const index = nodeElement.elements.findIndex(
              (item) => item === elm.node
            );
            if (index !== undefined && index >= 0) {
              newElements = newElements.concat(
                nodeElement.elements.slice(0, index)
              );
              newElements = newElements.concat(elm.node.elements);
              newElements = newElements.concat(
                nodeElement.elements.slice(index + 1)
              );
              node.elements = newElements;

              if (elm.action === ParseHTMLToXMLNodeActions.TEXTTOELEMENTS) {
                resultAction = elm.action;
              }
            }
          }
        }
      });
    }
    return resultAction;
  };

  const checkForQuote = (
    data: string,
    elements: Array<XMLElement>
  ): boolean => {
    const quoteList: Array<string> = data.split('"');
    if (quoteList.length > 1) {
      for (let j = 0; j < quoteList.length; j++) {
        if (quoteList[j].length > 0) {
          elements.push({
            type: "element",
            name: "text",
            elements: [
              {
                type: "text",
                text:
                  quoteList[j][0] === " " ||
                  quoteList[j][quoteList[j].length - 1] === " "
                    ? `"${quoteList[j]}"`
                    : quoteList[j],
              },
            ],
          });
        }
        if (j !== quoteList.length - 1) {
          elements.push({
            type: "element",
            name: "symbol",
            elements: [
              {
                type: "text",
                text: 34,
              },
            ],
          });
        }
      }
    } else if (data.length > 0) {
      elements.push({
        type: "element",
        name: "text",
        elements: [
          {
            type: "text",
            text:
              data[0] === " " || data[data.length - 1] === " "
                ? `"${data}"`
                : data,
          },
        ],
      });
      return true;
    }
    return false;
  };

  if (node.type !== undefined) {
    if (node.type === "element") {
      if (node.name !== undefined) {
        switch (node.name) {
          case "p":
            node.name = "paragraph";
            if (node.elements === undefined || node.elements.length === 0) {
              node.elements = [
                {
                  type: "element",
                  name: "text",
                  elements: [
                    {
                      type: "text",
                      text: "",
                    },
                  ],
                },
              ];
            } else {
              action = parseChild(node);
            }
            break;

          case "b":
          case "i":
          case "u":
            if (
              parent !== node &&
              (parent.name === "paragraph" || parent.name === "text") &&
              parent.elements !== undefined &&
              parent.elements.length === 1
            ) {
              parent.attributes = {
                ...parent.attributes,
                ...(HTMLToAttributes as any)[node.name],
              };
              parent.elements = node.elements;
              action = parseChild(parent);
            } else {
              node.attributes = {
                ...node.attributes,
                ...(HTMLToAttributes as any)[node.name],
              };
              node.name = "text";
              action = parseChild(node);
            }
            break;

          case "span":
            node.name = "text";
            action = parseChild(node);
            break;

          case "li":
            if (
              parent !== node &&
              parent.name !== undefined &&
              (parent.name === "ol" || parent.name === "ul")
            ) {
              node.attributes = {
                ...node.attributes,
                alignment: "1",
                leftindent: "60",
                leftsubindent: "60",
                bulletstyle: parent.name === "ol" ? "4353" : "512",
                bulletnumber: lastListSeq.toString(),
                liststyle:
                  parent.name === "ol" ? "Numbered List" : "Bullet List",
              };
              if (parent.name === "ul")
                node.attributes = {
                  ...node.attributes,
                  bulletname: "standard/circle",
                };
              node.name = "paragraph";
              parseChild(node);
            }
            break;

          case "ul":
          case "ol":
            if (
              node.elements !== undefined &&
              node.elements.length > 0 &&
              parent !== node &&
              parent.elements &&
              parent.elements.length > 0
            ) {
              parseChild(node);
              action = ParseHTMLToXMLNodeActions.COPYCHILD;
            } else {
              action = ParseHTMLToXMLNodeActions.DELETE;
            }
            break;

          default:
            parseChild(node);
            break;
        }
      }
    } else if (node.type === "text") {
      if (node.text !== undefined) {
        node.type = "element";
        const { text } = node;
        if (text !== undefined && typeof text === "string" && text.length > 0) {
          const elements: Array<XMLElement> = [];
          const tabList = text.split("&nbsp;");
          if (tabList.length > 1) {
            for (let i = 0; i < tabList.length; i++) {
              checkForQuote(tabList[i], elements);
              if (i !== tabList.length - 1) {
                elements.push({
                  type: "element",
                  name: "symbol",
                  elements: [
                    {
                      type: "text",
                      text: 9,
                    },
                  ],
                });
              }
            }
            node.text = undefined;
            node.name = "paragraph";
            node.elements = elements;
            if (parent.type === "paragraph") {
              action = ParseHTMLToXMLNodeActions.COPYCHILD;
            } else {
              action = ParseHTMLToXMLNodeActions.TEXTTOELEMENTS;
            }
          } else {
            const isSelf = checkForQuote(text, elements);
            if (isSelf) {
              if (parent.name !== undefined && parent.name !== "text") {
                node.text = undefined;
                node.type = elements[0].type;
                node.name = elements[0].name;
                node.elements = elements[0].elements;
              } else {
                node.text = text;
                node.type = "text";
                node.elements = undefined;
              }
            } else {
              node.text = undefined;
              node.type = "element";
              node.name = "paragraph";
              node.elements = elements;
              if (parent.name === "paragraph") {
                action = ParseHTMLToXMLNodeActions.COPYCHILD;
              } else {
                action = ParseHTMLToXMLNodeActions.TEXTTOELEMENTS;
              }
            }
          }
        } else if (parent.name !== undefined && parent.name !== "text") {
          node.text = undefined;
          node.name = "text";
          node.elements = [
            {
              type: "text",
              text,
            },
          ];
        } else {
          node.text = text;
          node.type = "text";
          node.elements = undefined;
        }
      }
    }
  } else if (node.elements !== undefined) {
    parseChild(node);
  }

  return action;
};

const convertHTMLToXML = (data: string): string => {
  const htmlStr: string = xml2json(data, { compact: false, spaces: 4 });
  const xmlElement: XMLElement = JSON.parse(htmlStr);
  parseHTMLToXMLNode(xmlElement, xmlElement);
  const res = js2xml(xmlElement, { compact: false, spaces: 4 });
  return res;
};

export const addXMLHeader = (xmlData: string): string => {
  let res = '<?xml version="1.0" encoding="UTF-8"?>';
  res += '<richtext version="1.0.0.0" xmlns="http://www.wxwidgets.org">';
  res +=
    '<paragraphlayout textcolor="#000000" fontpointsize="9" fontfamily="70" fontstyle="90" fontweight="90" fontunderlined="0" fontface="Segoe UI" alignment="1" parspacingafter="10" parspacingbefore="0" linespacing="10">';
  res += xmlData;
  res += "</paragraphlayout>";
  res += "</richtext>";
  return res;
};

export const convertDraftJSToXML = (editorState: EditorState): string => {
  const rawContentState = convertToRaw(editorState.getCurrentContent());
  const htmlElement = toDraftJsHtml(draftToHtml(rawContentState));
  let htmlToXml = addXMLHeader(htmlElement);
  htmlToXml = convertHTMLToXML(htmlToXml);
  return htmlToXml;
};
export default {};
