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

import { isSearchMatching } from "../stringUtils";

describe("stringUtils", () => {
  describe("isSearchMatching()", () => {
    test("should match a single search against a single value", () => {
      expect(isSearchMatching("test", "test")).toBeTruthy();
      expect(isSearchMatching("TEST", "test")).toBeTruthy();
      expect(isSearchMatching("es", "test")).toBeTruthy();
      expect(isSearchMatching("t", "TesT")).toBeTruthy();
      expect(isSearchMatching("", "test")).toBeTruthy();
    });

    test("should not match when single search doesn't exist in single value", () => {
      expect(isSearchMatching("testd", "test")).toBeFalsy();
      expect(isSearchMatching("a", "test")).toBeFalsy();
    });

    test("should match a single search against multiple values", () => {
      expect(isSearchMatching("test2", ["test1", "test2"])).toBeTruthy();
      expect(isSearchMatching("TEST2", ["test1", "test2"])).toBeTruthy();
      expect(isSearchMatching("es", ["test1", "test2"])).toBeTruthy();
      expect(isSearchMatching("t", ["TesT1", "TesT2"])).toBeTruthy();
      expect(isSearchMatching("", ["TesT1", "TesT2"])).toBeTruthy();
    });

    test("should not match when single search doesn't exist in any value", () => {
      expect(isSearchMatching("test3", ["test1", "test2"])).toBeFalsy();
      expect(isSearchMatching("TEST3", ["test1", "test2"])).toBeFalsy();
      expect(isSearchMatching("3", ["test1", "test2"])).toBeFalsy();
      expect(isSearchMatching("a", ["TesT1", "TesT2"])).toBeFalsy();
    });

    test("should match when any search term is found in a single value", () => {
      expect(isSearchMatching(["test"], "test")).toBeTruthy();
      expect(isSearchMatching(["a", "test"], "test")).toBeTruthy();
      expect(isSearchMatching(["a", "TEST"], "test")).toBeTruthy();
      expect(isSearchMatching(["a", "t"], "TesT")).toBeTruthy();
      expect(isSearchMatching([""], "test")).toBeTruthy();
    });

    test("should not match when all search terms are missing from a single value", () => {
      expect(isSearchMatching(["testd"], "test")).toBeFalsy();
      expect(isSearchMatching(["a", "b"], "test")).toBeFalsy();
      expect(isSearchMatching(["a", "TESTD"], "test")).toBeFalsy();
      expect(isSearchMatching([], "test")).toBeFalsy();
    });

    test("should match when any search term is found across multiple values", () => {
      expect(isSearchMatching(["test1", "test2"], ["test2", "test3"])).toBeTruthy();
      expect(isSearchMatching(["TEST", "a"], ["test2", "test3"])).toBeTruthy();
      expect(isSearchMatching(["t", "a"], ["TesT2", "TesT3"])).toBeTruthy();
      expect(isSearchMatching(["", "t"], ["TesT2", "TesT3"])).toBeTruthy();
      expect(isSearchMatching([""], ["TesT2", "TesT3"])).toBeTruthy();
    });

    test("should not match when all search terms are missing from multiple values", () => {
      expect(isSearchMatching(["test1", "test2"], ["test3", "test4"])).toBeFalsy();
      expect(isSearchMatching(["TEST1"], ["test3", "test4"])).toBeFalsy();
      expect(isSearchMatching([], ["test3", "test4"])).toBeFalsy();
    });
  });
});
