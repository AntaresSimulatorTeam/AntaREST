/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { describe, expect, it } from "vitest";
import {
  compactSemanticVersion,
  getHighestVersion,
  getSemanticVersionOptions,
  MAX_SEMVER,
  toSemanticVersion,
  ZERO_SEMVER,
} from "../versionUtils";

describe("versionUtils", () => {
  describe("constants", () => {
    it("ZERO_SEMVER", () => {
      expect(ZERO_SEMVER).toBe("0.0.0");
    });

    it("MAX_SEMVER", () => {
      expect(MAX_SEMVER).toBe(
        `${Number.MAX_SAFE_INTEGER}.${Number.MAX_SAFE_INTEGER}.${Number.MAX_SAFE_INTEGER}`,
      );
    });
  });

  // -------------------------------------------------------------

  describe("toSemanticVersion()", () => {
    it("converts number between 0 to 99 to semantic version", () => {
      expect(toSemanticVersion(0)).toBe("0.0.0");
      expect(toSemanticVersion(9)).toBe("9.0.0");
      expect(toSemanticVersion(99)).toBe("99.0.0");
    });

    it("converts number superior or equal to 100 to semantic version", () => {
      expect(toSemanticVersion(934)).toBe("9.3.4");
      expect(toSemanticVersion(1011)).toBe("10.1.1");
      expect(toSemanticVersion(10112)).toBe("101.1.2");
    });

    it("returns `ZERO_SEMVER` for invalid number values", () => {
      expect(toSemanticVersion(-1)).toBe(ZERO_SEMVER);
      expect(toSemanticVersion(9.3)).toBe(ZERO_SEMVER);
      expect(toSemanticVersion(NaN)).toBe(ZERO_SEMVER);
      expect(toSemanticVersion((Number.MAX_SAFE_INTEGER + 1) * 100)).toBe(ZERO_SEMVER);
    });

    it("converts compact version to semantic version", () => {
      expect(toSemanticVersion("9")).toBe("9.0.0");
      expect(toSemanticVersion("9.3")).toBe("9.3.0");
    });

    it("converts version with extra components to semantic version", () => {
      expect(toSemanticVersion("9.3.4.1")).toBe("9.3.4");
      expect(toSemanticVersion("9.3.44.1")).toBe("9.3.44");
    });

    it("coerces semver-like strings", () => {
      expect(toSemanticVersion("v1.2.3")).toBe("1.2.3");
      expect(toSemanticVersion(">=2.4.0")).toBe("2.4.0");
    });

    it("returns `ZERO_SEMVER` for invalid string values", () => {
      expect(toSemanticVersion("")).toBe(ZERO_SEMVER);
      expect(toSemanticVersion("not-a-version")).toBe(ZERO_SEMVER);
    });
  });

  // -------------------------------------------------------------

  describe("compactSemanticVersion()", () => {
    it("compacts x.0.0 to x", () => {
      expect(compactSemanticVersion("9.0.0")).toBe("9");
    });

    it("compacts x.y.0 to x.y", () => {
      expect(compactSemanticVersion("9.3.0")).toBe("9.3");
    });

    it("keeps x.y.z unchanged", () => {
      expect(compactSemanticVersion("9.3.4")).toBe("9.3.4");
    });

    it("returns original input for invalid versions", () => {
      const input = "not-a-version";
      expect(compactSemanticVersion(input)).toBe(input);
    });
  });

  // -------------------------------------------------------------

  describe("getHighestVersion()", () => {
    it("returns the highest semantic version", () => {
      const versions = ["1.2.0", "1.10.0", "2.0.0", "1.9.9"];
      expect(getHighestVersion(versions)).toBe("2.0.0");
    });

    it("returns null for empty list", () => {
      expect(getHighestVersion([])).toBeNull();
    });

    it("returns null for list with invalid semantic version(s)", () => {
      const versions = ["1.2", "1", "2.0.0", "1.9.9"];
      expect(getHighestVersion(versions)).toBeNull();
    });
  });

  // -------------------------------------------------------------

  describe("getSemanticVersionOptions()", () => {
    it("maps versions to options with compact labels", () => {
      expect(getSemanticVersionOptions(["9.0.0", "9.3.0", "9.3.4"])).toEqual([
        { value: "9.0.0", label: "9" },
        { value: "9.3.0", label: "9.3" },
        { value: "9.3.4", label: "9.3.4" },
      ]);
    });

    it("maps versions to options with compact labels while filtering out `ZERO_SEMVER`", () => {
      expect(getSemanticVersionOptions(["9.0.0", ZERO_SEMVER, "9.3.4"])).toEqual([
        { value: "9.0.0", label: "9" },
        { value: "9.3.4", label: "9.3.4" },
      ]);
    });

    it("maps versions to options with compact labels while filtering out invalid semantic version(s)", () => {
      expect(getSemanticVersionOptions(["9.0", "9.3", "9.3.4", ""])).toEqual([
        { value: "9.3.4", label: "9.3.4" },
      ]);
    });
  });
});
