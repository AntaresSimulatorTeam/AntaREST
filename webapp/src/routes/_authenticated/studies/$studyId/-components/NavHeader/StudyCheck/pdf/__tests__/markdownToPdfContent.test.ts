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

import { markdownToPdfContent } from "../markdownToPdfContent";

describe("markdownToPdfContent", () => {
  test("gives nothing for an empty text", () => {
    expect(markdownToPdfContent("  \n")).toEqual([]);
  });

  test("keeps the emphasis of a paragraph", () => {
    expect(markdownToPdfContent("Plain **bold**, *italic* and `fr / nuclear`.")).toEqual([
      {
        text: [
          "Plain ",
          { text: ["bold"], bold: true },
          ", ",
          { text: ["italic"], italics: true },
          " and ",
          { text: "fr / nuclear", style: "markdownInlineCode" },
          ".",
        ],
        style: "markdownParagraph",
      },
    ]);
  });

  test("separates paragraphs and joins the lines of a paragraph", () => {
    expect(markdownToPdfContent("First line\nsame paragraph.\n\nSecond paragraph.")).toEqual([
      { text: ["First line same paragraph."], style: "markdownParagraph" },
      { text: ["Second paragraph."], style: "markdownParagraph" },
    ]);
  });

  test("keeps a line break asked for by the author", () => {
    expect(markdownToPdfContent("First line  \nsecond line")).toEqual([
      { text: ["First line", "\n", "second line"], style: "markdownParagraph" },
    ]);
  });

  test("distinguishes the titles from the subtitles", () => {
    expect(markdownToPdfContent("# Report\n\n## Errors\n\n### Hydro")).toEqual([
      { text: ["Report"], style: "markdownHeading" },
      { text: ["Errors"], style: "markdownHeading" },
      { text: ["Hydro"], style: "markdownSubheading" },
    ]);
  });

  test("converts a bullet list, with a numbered list nested in an item", () => {
    const markdown = [
      "- Check **fr**",
      "- Then:",
      "",
      "  3. open the area",
      "  4. fix the cost",
    ].join("\n");

    expect(markdownToPdfContent(markdown)).toEqual([
      {
        ul: [
          { text: ["Check ", { text: ["fr"], bold: true }] },
          {
            stack: [
              { text: ["Then:"] },
              {
                ol: [{ text: ["open the area"] }, { text: ["fix the cost"] }],
                start: 3,
                style: "markdownList",
              },
            ],
          },
        ],
        style: "markdownList",
      },
    ]);
  });

  test("keeps the layout of a block of code", () => {
    expect(markdownToPdfContent("```ini\n[general]\n  horizon = 2030\n```")).toEqual([
      { text: "[general]\n  horizon = 2030", style: "markdownCode", preserveLeadingSpaces: true },
    ]);
  });

  test("keeps a quotation apart from the text", () => {
    expect(markdownToPdfContent("> To confirm with the author.")).toEqual([
      { stack: [{ text: ["To confirm with the author."] }], style: "markdownQuote" },
    ]);
  });

  test("makes a link clickable", () => {
    expect(markdownToPdfContent("See [the docs](https://antares-web.readthedocs.io).")).toEqual([
      {
        text: [
          "See ",
          {
            text: ["the docs"],
            link: "https://antares-web.readthedocs.io",
            style: "markdownLink",
          },
          ".",
        ],
        style: "markdownParagraph",
      },
    ]);
  });

  test("rewrites the characters the font of the PDF cannot draw", () => {
    expect(markdownToPdfContent("✅ fr → de")).toEqual([
      { text: ["[OK] fr -> de"], style: "markdownParagraph" },
    ]);
  });

  test("ignores a horizontal rule", () => {
    expect(markdownToPdfContent("Before\n\n---\n\nAfter")).toEqual([
      { text: ["Before"], style: "markdownParagraph" },
      { text: ["After"], style: "markdownParagraph" },
    ]);
  });
});
