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

import { buildKey } from "../reactUtils";

/**
 * Joins lines with `\n` to keep the expected keys readable.
 *
 * @param values - The values to join.
 * @returns The joined string.
 */
const lines = (...values: string[]) => values.join("\n");

describe("reactUtils", () => {
  describe("buildKey()", () => {
    test("should build a key from primitive values", () => {
      expect(buildKey("a", 1, "1", true, "true")).toBe(lines('"a"', "1", '"1"', "true", '"true"'));
    });

    test("should build a key from arrays", () => {
      expect(buildKey(["a", "b"], [1, 2, "3"], [true, false, "true"])).toBe(
        lines("[2]", '"a"', '"b"', "[3]", "1", "2", '"3"', "[3]", "true", "false", '"true"'),
      );
    });

    test("should preserve array order", () => {
      expect(buildKey(["b", "a", 1, true])).toBe(lines("[4]", '"b"', '"a"', "1", "true"));
      expect(buildKey([1, true, "a", "b"])).toBe(lines("[4]", "1", "true", '"a"', '"b"'));
    });

    test("should escape line breaks in values", () => {
      expect(buildKey(["a\nb"])).toBe(lines("[1]", '"a\\nb"'));
    });

    test("should build a key from objects with sorted keys", () => {
      const key = lines("{2}", '"a"=1', '"b"="2"', "{1}", '"c"=true');

      expect(buildKey({ a: 1, b: "2" }, { c: true })).toBe(key);
      // Different insertion order must produce the same key
      expect(buildKey({ b: "2", a: 1 }, { c: true })).toBe(key);
    });

    test("should escape object keys", () => {
      expect(buildKey({ "a\nb": 1 })).toBe(lines("{1}", '"a\\nb"=1'));
      expect(buildKey({ '"a"': 1 }, "x")).toBe(lines("{1}", '"\\"a\\""=1', '"x"'));
    });

    test("should not collide on '=' inside keys or values", () => {
      expect(buildKey({ "a=1": 2 })).not.toBe(buildKey({ a: "1=2" }));
      expect(buildKey({ "a=": "b" })).not.toBe(buildKey({ a: "=b" }));
    });

    test("should build a key from mixed types", () => {
      expect(buildKey("a", ["b", "c"], { d: 4 })).toBe(
        lines('"a"', "[2]", '"b"', '"c"', "{1}", '"d"=4'),
      );
    });

    test("should differentiate a number from its string representation", () => {
      expect(buildKey(1)).not.toBe(buildKey("1"));
      expect(buildKey(true)).not.toBe(buildKey("true"));
    });

    test("should not collide between an array and separate values", () => {
      expect(buildKey(["a", "b"])).not.toBe(buildKey("a", "b"));
    });

    test("should differentiate empty collections", () => {
      const keys = [buildKey(), buildKey([]), buildKey({}), buildKey(""), buildKey([""])];
      expect(new Set(keys).size).toBe(keys.length);
      expect(buildKey([], "a")).not.toBe(buildKey("a"));
    });

    test("should not let a string mimic a size header", () => {
      expect(buildKey("[1]", "a")).not.toBe(buildKey(["a"]));
      expect(buildKey("{0}")).not.toBe(buildKey({}));
    });

    test("should differentiate special numbers", () => {
      const keys = [NaN, Infinity, -Infinity, -0, 0].map((n) => buildKey(n));
      expect(new Set(keys).size).toBe(keys.length);
      expect(buildKey(NaN)).toBe("NaN");
      expect(buildKey(Infinity)).toBe("Infinity");
      expect(buildKey(-Infinity)).toBe("-Infinity");
      expect(buildKey(-0)).toBe("-0");
    });
  });
});
