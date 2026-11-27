/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { ListItem, PhrasingContent, RootContent } from "mdast";
import { fromMarkdown } from "mdast-util-from-markdown";
import type { Content, StyleDictionary } from "pdfmake/interfaces";
import { sanitizePdfText } from "./sanitizePdfText";

const SUBHEADING_DEPTH = 3;

export const MARKDOWN_STYLES: StyleDictionary = {
  markdownParagraph: { margin: [0, 0, 0, 6] },
  markdownHeading: { bold: true, fontSize: 11, margin: [0, 6, 0, 4] },
  markdownSubheading: { bold: true, margin: [0, 4, 0, 3] },
  markdownList: { margin: [0, 0, 0, 6] },
  markdownCode: { fontSize: 8.5, color: "#344054", margin: [8, 0, 0, 6] },
  markdownInlineCode: { background: "#F2F4F7" },
  markdownLink: { color: "#175CD3", decoration: "underline" },
  markdownQuote: { italics: true, color: "#475467", margin: [8, 0, 0, 6] },
};

interface BlockOptions {
  /** Inside a list item or a quotation, where the container sets the spacing. */
  isNested: boolean;
}

function convertPhrasing(nodes: PhrasingContent[]): Content[] {
  return nodes.map((node): Content => {
    switch (node.type) {
      case "text":
        return sanitizePdfText(node.value.replace(/\n/g, " "));
      case "break":
        return "\n";
      case "strong":
        return { text: convertPhrasing(node.children), bold: true };
      case "emphasis":
        return { text: convertPhrasing(node.children), italics: true };
      case "inlineCode":
        return { text: sanitizePdfText(node.value), style: "markdownInlineCode" };
      case "link":
        return { text: convertPhrasing(node.children), link: node.url, style: "markdownLink" };
      case "image":
        return sanitizePdfText(node.alt ?? "");
      case "html":
        return sanitizePdfText(node.value);
      default:
        return "";
    }
  });
}

function convertListItem(item: ListItem): Content {
  const blocks = convertBlocks(item.children, { isNested: true });
  return blocks.length === 1 ? blocks[0] : { stack: blocks };
}

function convertBlock(node: RootContent, { isNested }: BlockOptions): Content[] {
  switch (node.type) {
    case "paragraph": {
      const text = convertPhrasing(node.children);
      return [isNested ? { text } : { text, style: "markdownParagraph" }];
    }
    case "heading":
      return [
        {
          text: convertPhrasing(node.children),
          style: node.depth < SUBHEADING_DEPTH ? "markdownHeading" : "markdownSubheading",
        },
      ];
    case "list": {
      const items = node.children.map(convertListItem);
      return [
        node.ordered
          ? { ol: items, start: node.start ?? 1, style: "markdownList" }
          : { ul: items, style: "markdownList" },
      ];
    }
    case "code":
      return [
        { text: sanitizePdfText(node.value), style: "markdownCode", preserveLeadingSpaces: true },
      ];
    case "blockquote":
      return [{ stack: convertBlocks(node.children, { isNested: true }), style: "markdownQuote" }];
    case "html":
      return [{ text: [sanitizePdfText(node.value)], style: "markdownParagraph" }];
    default:
      return [];
  }
}

function convertBlocks(nodes: RootContent[], options: BlockOptions): Content[] {
  return nodes.flatMap((node) => convertBlock(node, options));
}

/**
 * Converts a text of the AI assistant to the content of a PDF. The text is read with the parser
 * of `react-markdown`, so that the PDF and the interface understand it the same way (CommonMark,
 * without tables).
 *
 * @param markdown - Text of the assistant (Markdown).
 * @returns The blocks of the text, with the styles of `MARKDOWN_STYLES`.
 */
export function markdownToPdfContent(markdown: string): Content[] {
  return convertBlocks(fromMarkdown(markdown).children, { isNested: false });
}
