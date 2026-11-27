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

import type { CheckFinding } from "@/services/api/assistant/types";
import type { DynamicContent, Node, NodeQueries } from "pdfmake/interfaces";
import {
  buildReportDocument,
  type CheckReportExport,
  type Translate,
} from "../buildReportDocument";

const HYDRO: CheckFinding = {
  rule: "hydro_generation_power",
  severity: "error",
  message: "Hydro inflows but no generating power.",
  objects: ["fr", "es"],
  count: 39,
};

const COST_WARNING: CheckFinding = {
  rule: "unsupplied_energy_cost",
  severity: "warning",
  message: "Unsupplied energy cost below the most expensive plant.",
  objects: ["de (100 < 180 EUR/MWh)"],
  count: 1,
};

const COST_INFO: CheckFinding = {
  rule: "unsupplied_energy_cost",
  severity: "info",
  message: "Unsupplied energy cost of 0.",
  objects: ["x_helper"],
  count: 1,
};

const EXPORT: CheckReportExport = {
  studyId: "study-1",
  studyName: "Reference 2030",
  generatedAt: new Date("2026-11-27T14:05:00Z"),
  language: "en",
  report: {
    summary: { error: 1, warning: 1, info: 1 },
    findings: [COST_INFO, HYDRO, COST_WARNING],
    notes: [],
  },
  verdict: "The study is **not ready** to be simulated.",
  explanations: {},
};

const translate: Translate = (key, options = {}) => {
  const values = Object.entries(options)
    .filter(([name]) => name !== "defaultValue")
    .map(([, value]) => String(value));
  return values.length > 0 ? `${key}:${values.join(",")}` : key;
};

function isContentNode(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function collectTexts(content: unknown): string[] {
  if (typeof content === "string") {
    return [content];
  }
  if (Array.isArray(content)) {
    return content.flatMap(collectTexts);
  }
  if (!isContentNode(content)) {
    return [];
  }
  const table = isContentNode(content.table) ? content.table.body : undefined;
  return [content.text, content.stack, content.ul, content.ol, content.columns, table].flatMap(
    collectTexts,
  );
}

function textsOf(data: CheckReportExport): string[] {
  return collectTexts(buildReportDocument(data, translate).content);
}

function collectUnbreakableBlocks(content: unknown): string[][] {
  if (Array.isArray(content)) {
    return content.flatMap(collectUnbreakableBlocks);
  }
  if (!isContentNode(content)) {
    return [];
  }
  if (content.unbreakable === true) {
    return [collectTexts(content)];
  }
  return collectUnbreakableBlocks([content.stack, content.columns]);
}

function findColumns(content: unknown): unknown[][] {
  if (Array.isArray(content)) {
    return content.flatMap(findColumns);
  }
  if (!isContentNode(content)) {
    return [];
  }
  return Array.isArray(content.columns) ? [content.columns] : findColumns(content.stack);
}

function laidOut(node: Pick<Node, "text" | "headlineLevel">): Node {
  return {
    ...node,
    pageNumbers: [1],
    pages: 1,
    stack: false,
    startPosition: {
      pageNumber: 1,
      pageOrientation: "portrait",
      pageInnerHeight: 754,
      pageInnerWidth: 515,
      left: 40,
      top: 700,
      verticalRatio: 0.9,
      horizontalRatio: 0,
    },
  };
}

function queriesWith(followingNodesOnPage: Node[]): NodeQueries {
  return {
    getFollowingNodesOnPage: () => followingNodesOnPage,
    getNodesOnNextPage: () => [],
    getPreviousNodesOnPage: () => [],
  };
}

function assertInOrder(texts: string[], expected: string[]) {
  const positions = expected.map((text) => texts.indexOf(text));

  expect(positions).not.toContain(-1);
  expect(positions).toEqual([...positions].sort((a, b) => a - b));
}

describe("buildReportDocument", () => {
  test("lists the findings from the most to the least severe, whatever their order", () => {
    assertInOrder(textsOf(EXPORT), [
      "study.check.severity.error (1)",
      HYDRO.message,
      "study.check.severity.warning (1)",
      COST_WARNING.message,
      "study.check.severity.info (1)",
      COST_INFO.message,
    ]);
  });

  test("names the rule of each finding", () => {
    assertInOrder(textsOf(EXPORT), [
      "study.check.rule.hydro_generation_power",
      HYDRO.message,
      "study.check.rule.unsupplied_energy_cost",
      COST_WARNING.message,
    ]);
  });

  test("leaves out the severities without any finding", () => {
    const texts = textsOf({
      ...EXPORT,
      report: { ...EXPORT.report, summary: { error: 1, warning: 0, info: 0 }, findings: [HYDRO] },
    });

    expect(texts).toContain("study.check.severity.error (1)");
    expect(texts).not.toContain("study.check.severity.warning (0)");
    expect(texts).not.toContain("study.check.severity.info (0)");
  });

  test("names the study and says when it was checked", () => {
    const document = buildReportDocument(EXPORT, translate);
    const texts = collectTexts(document.content);

    expect(texts).toContain("Reference 2030");
    expect(texts).toContain("study.check.pdf.generatedOn:November 27, 2026 at 2:05 PM");
    expect(texts).toContain("study-1");
    expect(document.info?.title).toBe("study.check.title - Reference 2030");
  });

  test("gives the verdict before the findings", () => {
    const texts = textsOf(EXPORT);

    assertInOrder(texts, ["not ready", "study.check.severity.error (1)"]);
  });

  test("lists the objects of a finding and says how many are not listed", () => {
    assertInOrder(textsOf(EXPORT), [
      HYDRO.message,
      "study.check.objects:39",
      "fr",
      "es",
      "study.check.moreObjects:37",
    ]);
  });

  test("does not announce other objects when they are all listed", () => {
    expect(textsOf(EXPORT)).not.toContain("study.check.moreObjects:0");
  });

  test("puts the explanation of a rule once, under its most severe finding", () => {
    const texts = textsOf({
      ...EXPORT,
      explanations: { unsupplied_energy_cost: "Shedding load is cheaper than these plants." },
    });

    assertInOrder(texts, [
      COST_WARNING.message,
      "study.check.pdf.explanation",
      "Shedding load is cheaper than these plants.",
      "study.check.explain.disclaimer",
      "study.check.severity.info (1)",
      COST_INFO.message,
    ]);
    expect(texts.filter((text) => text === "study.check.pdf.explanation")).toHaveLength(1);
  });

  test("ends with the summary then the review of the assistant, when they were asked for", () => {
    const texts = textsOf({
      ...EXPORT,
      summary: "Fix the hydro power first.",
      review: "The cost of `de` is out of line.",
    });

    assertInOrder(texts, [
      COST_INFO.message,
      "study.check.summary.title",
      "Fix the hydro power first.",
      "study.check.summary.disclaimer",
      "study.check.review.title",
      "de",
      "study.check.review.disclaimer",
    ]);
  });

  test("has no section of the assistant when nothing was asked to it", () => {
    const texts = textsOf(EXPORT);

    expect(texts).not.toContain("study.check.summary.title");
    expect(texts).not.toContain("study.check.review.title");
    expect(texts).not.toContain("study.check.pdf.explanation");
  });

  test("says that the rules found nothing", () => {
    const texts = textsOf({
      ...EXPORT,
      report: { ...EXPORT.report, summary: { error: 0, warning: 0, info: 0 }, findings: [] },
    });

    expect(texts).toContain("study.check.noFinding");
    expect(texts.some((text) => text.startsWith("study.check.severity."))).toBe(false);
  });

  test("keeps the notes of the rules after the findings", () => {
    const note = "3 matrices could not be read and were not checked.";
    const texts = textsOf({ ...EXPORT, report: { ...EXPORT.report, notes: [note] } });

    assertInOrder(texts, [COST_INFO.message, note]);
  });

  test("gives only the first objects of a finding which has many", () => {
    const objects = Array.from({ length: 30 }, (_, index) => `constraint_${index + 1}`);
    const texts = textsOf({
      ...EXPORT,
      report: { ...EXPORT.report, findings: [{ ...HYDRO, objects, count: 308 }] },
    });

    expect(texts.filter((text) => text.startsWith("constraint_"))).toEqual(objects.slice(0, 10));
    expect(texts).toContain("study.check.moreObjects:298");
  });

  test("writes a long list of objects in two columns", () => {
    const objects = ["at", "be", "ch", "cz", "de", "dk", "es", "fi", "fr"];
    const finding = { ...HYDRO, objects, count: 39 };
    const document = buildReportDocument(
      { ...EXPORT, report: { ...EXPORT.report, findings: [finding] } },
      translate,
    );

    expect(findColumns(document.content).map((columns) => columns.map(collectTexts))).toEqual([
      [
        ["at", "be", "ch", "cz", "de"],
        ["dk", "es", "fi", "fr", "study.check.moreObjects:30"],
      ],
    ]);
  });

  test("writes a short list of objects in one column", () => {
    expect(findColumns(buildReportDocument(EXPORT, translate).content)).toEqual([]);
  });

  test("keeps the title of a severity on the page of its first finding", () => {
    const blocks = collectUnbreakableBlocks(buildReportDocument(EXPORT, translate).content);

    expect(blocks).toContainEqual(
      expect.arrayContaining(["study.check.severity.error (1)", HYDRO.message, "fr", "es"]),
    );
  });

  test("keeps a finding on one page, and lets the explanation of its rule go on the next", () => {
    const explanation = "Shedding load is cheaper than these plants.";
    const document = buildReportDocument(
      { ...EXPORT, explanations: { unsupplied_energy_cost: explanation } },
      translate,
    );
    const blocks = collectUnbreakableBlocks(document.content);

    expect(blocks).toContainEqual(
      expect.arrayContaining([COST_WARNING.message, "de (100 < 180 EUR/MWh)"]),
    );
    expect(blocks.flat()).not.toContain(explanation);
  });

  test("does not leave the title of a text of the assistant alone at the bottom of a page", () => {
    const { pageBreakBefore } = buildReportDocument(EXPORT, translate);
    const title = laidOut({ headlineLevel: 1, text: "study.check.summary.title" });
    const paragraph = laidOut({ text: "Fix the hydro power first." });

    expect(pageBreakBefore?.(title, queriesWith([]))).toBe(true);
    expect(pageBreakBefore?.(title, queriesWith([paragraph]))).toBe(false);
    expect(pageBreakBefore?.(paragraph, queriesWith([]))).toBe(false);
  });

  test("numbers the pages", () => {
    const footer = buildReportDocument(EXPORT, translate).footer as DynamicContent;
    const content = footer(2, 5, { width: 595, height: 842, orientation: "portrait" });

    expect(collectTexts(content)).toContain("study.check.pdf.page:2,5");
  });
});
