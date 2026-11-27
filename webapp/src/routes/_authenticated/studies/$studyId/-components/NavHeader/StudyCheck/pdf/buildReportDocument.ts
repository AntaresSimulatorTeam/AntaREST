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

import type {
  CheckFinding,
  CheckLanguage,
  CheckReport,
  CheckSeverity,
} from "@/services/api/assistant/types";
import type { Content, StyleDictionary, TDocumentDefinitions } from "pdfmake/interfaces";
import { getVerdictSeverity, SEVERITIES } from "../utils";
import { MARKDOWN_STYLES, markdownToPdfContent } from "./markdownToPdfContent";
import { sanitizePdfText } from "./sanitizePdfText";

/** Everything the report of a check shows, at the time of the export. */
export interface CheckReportExport {
  studyId: string;
  studyName: string;
  generatedAt: Date;
  language: CheckLanguage;
  report: CheckReport;
  /** Whether the study can be simulated (Markdown). */
  verdict: string;
  /** Explanations of the AI assistant which are finished, by rule (Markdown). */
  explanations: Record<string, string>;
  /** Summary of the findings by the AI assistant, once written (Markdown). */
  summary?: string;
  /** Review of the study by the AI assistant, once written (Markdown). */
  review?: string;
}

export type Translate = (key: string, options?: Record<string, unknown>) => string;

interface Palette {
  accent: string;
  tint: string;
}

const INK = "#1D2939";
const MUTED = "#667085";
const PAGE_MARGIN = 40;
const A4_WIDTH = 595.28;
const CONTENT_WIDTH = A4_WIDTH - 2 * PAGE_MARGIN;
const MAX_LISTED_OBJECTS = 10;
const MAX_OBJECTS_IN_ONE_COLUMN = 8;
const SECTION_HEADLINE_LEVEL = 1;

const PALETTES: Record<CheckSeverity | "success" | "assistant", Palette> = {
  error: { accent: "#B42318", tint: "#FEF3F2" },
  warning: { accent: "#B54708", tint: "#FFFAEB" },
  info: { accent: "#175CD3", tint: "#EFF8FF" },
  success: { accent: "#067647", tint: "#ECFDF3" },
  assistant: { accent: "#98A2B3", tint: "#F9FAFB" },
};

const STYLES: StyleDictionary = {
  ...MARKDOWN_STYLES,
  documentTitle: { fontSize: 10, color: MUTED, characterSpacing: 0.4 },
  studyName: { fontSize: 20, bold: true, margin: [0, 2, 0, 2] },
  generation: { fontSize: 8.5, color: MUTED, margin: [0, 0, 0, 14] },
  severityTitle: { fontSize: 13, bold: true, margin: [0, 10, 0, 3] },
  sectionTitle: { fontSize: 13, bold: true, margin: [0, 14, 0, 6] },
  ruleName: { bold: true, fontSize: 10.5, margin: [0, 8, 0, 2] },
  objectsCaption: { fontSize: 8.5, color: MUTED, margin: [0, 4, 0, 1] },
  objects: { fontSize: 9, margin: [4, 0, 0, 6] },
  explanationTitle: { bold: true, fontSize: 9, color: MUTED, margin: [0, 0, 0, 4] },
  disclaimer: { fontSize: 8, italics: true, color: MUTED },
  note: { fontSize: 9, color: MUTED, margin: [0, 6, 0, 0] },
  footer: { fontSize: 8, color: MUTED },
};

function formatDate(date: Date, language: CheckLanguage): string {
  return new Intl.DateTimeFormat(language, { dateStyle: "long", timeStyle: "short" }).format(date);
}

function frame(body: Content[], { accent, tint }: Palette): Content {
  return {
    table: { widths: ["*"], body: [[{ stack: body, fillColor: tint }]] },
    layout: {
      hLineWidth: () => 0,
      vLineWidth: (columnIndex) => (columnIndex === 0 ? 2.5 : 0),
      vLineColor: () => accent,
      paddingLeft: () => 10,
      paddingRight: () => 10,
      paddingTop: () => 7,
      paddingBottom: () => 3,
    },
    margin: [0, 2, 0, 8],
  };
}

function underline(color: string): Content {
  return {
    canvas: [
      { type: "line", x1: 0, y1: 0, x2: CONTENT_WIDTH, y2: 0, lineWidth: 1.5, lineColor: color },
    ],
    margin: [0, 0, 0, 2],
  };
}

function buildHeader(
  { studyId, studyName, generatedAt, language }: CheckReportExport,
  t: Translate,
) {
  const date = sanitizePdfText(formatDate(generatedAt, language));

  return [
    { text: t("study.check.title").toUpperCase(), style: "documentTitle" },
    { text: sanitizePdfText(studyName), style: "studyName" },
    { text: [t("study.check.pdf.generatedOn", { date }), "  ·  ", studyId], style: "generation" },
  ] satisfies Content[];
}

function buildVerdict({ report, verdict }: CheckReportExport, t: Translate): Content[] {
  if (report.findings.length === 0) {
    return [
      frame([{ text: t("study.check.noFinding"), style: "markdownParagraph" }], PALETTES.success),
    ];
  }
  return verdict
    ? [frame(markdownToPdfContent(verdict), PALETTES[getVerdictSeverity(report)])]
    : [];
}

function buildExplanation(explanation: string, t: Translate): Content {
  return frame(
    [
      { text: t("study.check.pdf.explanation"), style: "explanationTitle" },
      ...markdownToPdfContent(explanation),
      { text: t("study.check.explain.disclaimer"), style: "disclaimer", margin: [0, 0, 0, 4] },
    ],
    PALETTES.assistant,
  );
}

function buildObjects(finding: CheckFinding, t: Translate): Content {
  const listedObjects = finding.objects.slice(0, MAX_LISTED_OBJECTS);
  const unlistedObjects = finding.count - listedObjects.length;
  const objects: Content[] = listedObjects.map(sanitizePdfText);

  if (unlistedObjects > 0) {
    objects.push({ text: t("study.check.moreObjects", { count: unlistedObjects }), color: MUTED });
  }
  if (objects.length <= MAX_OBJECTS_IN_ONE_COLUMN) {
    return { ul: objects, style: "objects" };
  }
  const firstColumnLength = Math.ceil(objects.length / 2);

  return {
    columns: [
      { ul: objects.slice(0, firstColumnLength) },
      { ul: objects.slice(firstColumnLength) },
    ],
    columnGap: 16,
    style: "objects",
  };
}

interface FindingContext {
  /** Title of the severity, for its first finding: both stay on the same page. */
  severityTitle: Content[];
  /** Explanation of the rule by the AI assistant (Markdown). */
  explanation?: string;
}

function buildFinding(
  finding: CheckFinding,
  { severityTitle, explanation }: FindingContext,
  t: Translate,
): Content[] {
  return [
    {
      stack: [
        ...severityTitle,
        {
          text: t(`study.check.rule.${finding.rule}`, { defaultValue: finding.rule }),
          style: "ruleName",
        },
        { text: sanitizePdfText(finding.message) },
        { text: t("study.check.objects", { count: finding.count }), style: "objectsCaption" },
        buildObjects(finding, t),
      ],
      unbreakable: true,
    },
    ...(explanation ? [buildExplanation(explanation, t)] : []),
  ];
}

function buildFindings({ report, explanations }: CheckReportExport, t: Translate): Content[] {
  const explainedRules = new Set<string>();

  const takeExplanation = (rule: string) => {
    if (explainedRules.has(rule)) {
      return undefined;
    }
    explainedRules.add(rule);
    return explanations[rule];
  };

  return SEVERITIES.flatMap((severity): Content[] => {
    const findings = report.findings.filter((finding) => finding.severity === severity);

    if (findings.length === 0) {
      return [];
    }
    const { accent } = PALETTES[severity];
    const severityTitle: Content[] = [
      {
        text: `${t(`study.check.severity.${severity}`)} (${findings.length})`,
        style: "severityTitle",
        color: accent,
      },
      underline(accent),
    ];

    return findings.flatMap((finding, index) =>
      buildFinding(
        finding,
        {
          severityTitle: index === 0 ? severityTitle : [],
          explanation: takeExplanation(finding.rule),
        },
        t,
      ),
    );
  });
}

function buildAssistantSection(
  title: string,
  text: string | undefined,
  disclaimer: string,
): Content[] {
  if (!text) {
    return [];
  }
  return [
    { text: title, style: "sectionTitle", headlineLevel: SECTION_HEADLINE_LEVEL },
    ...markdownToPdfContent(text),
    { text: disclaimer, style: "disclaimer" },
  ];
}

/**
 * Builds the PDF report of a check: the verdict, the findings of the rules from the most to the
 * least severe, then what the AI assistant wrote on request (explanations under the rule
 * concerned, summary, review).
 *
 * @param data - What the report shows.
 * @param t - Translation function, in the language of the report.
 * @returns The definition of the document, for `pdfmake`.
 */
export function buildReportDocument(data: CheckReportExport, t: Translate): TDocumentDefinitions {
  const studyName = sanitizePdfText(data.studyName);

  return {
    info: { title: `${t("study.check.title")} - ${data.studyName}` },
    pageSize: "A4",
    pageMargins: [PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, 48],
    defaultStyle: { fontSize: 9.5, lineHeight: 1.25, color: INK },
    styles: STYLES,
    content: [
      ...buildHeader(data, t),
      ...buildVerdict(data, t),
      ...buildFindings(data, t),
      ...data.report.notes.map((note): Content => ({ text: sanitizePdfText(note), style: "note" })),
      ...buildAssistantSection(
        t("study.check.summary.title"),
        data.summary,
        t("study.check.summary.disclaimer"),
      ),
      ...buildAssistantSection(
        t("study.check.review.title"),
        data.review,
        t("study.check.review.disclaimer"),
      ),
    ],
    pageBreakBefore: (node, { getFollowingNodesOnPage }) =>
      node.headlineLevel === SECTION_HEADLINE_LEVEL && getFollowingNodesOnPage().length === 0,
    footer: (currentPage, pageCount) => ({
      columns: [
        { text: `Antares Web  ·  ${studyName}` },
        {
          text: t("study.check.pdf.page", { current: currentPage, total: pageCount }),
          alignment: "right",
        },
      ],
      style: "footer",
      margin: [PAGE_MARGIN, 18, PAGE_MARGIN, 0],
    }),
  };
}
