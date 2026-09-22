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

import { getScheduleRunAt } from "../utils";

// Tests run with TZ=UTC, so local time === UTC
describe("getScheduleRunAt", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test("returns undefined for 'now'", () => {
    expect(getScheduleRunAt("now")).toBeUndefined();
  });

  test("'tonight7pm' returns today at 7 PM", () => {
    vi.setSystemTime(new Date("2026-08-06T10:00:00Z")); // Thursday
    expect(getScheduleRunAt("tonight7pm")).toBe("2026-08-06T19:00:00.000Z");
  });

  test("'tonight9pm' returns today at 9 PM", () => {
    vi.setSystemTime(new Date("2026-08-06T10:00:00Z")); // Thursday
    expect(getScheduleRunAt("tonight9pm")).toBe("2026-08-06T21:00:00.000Z");
  });

  test("'tonight7pm' returns today at 7 PM even if it has passed (caught by validation)", () => {
    vi.setSystemTime(new Date("2026-08-06T20:00:00Z")); // Thursday 8 PM
    expect(getScheduleRunAt("tonight7pm")).toBe("2026-08-06T19:00:00.000Z");
  });

  test("'weekend' returns the next Friday at 7 PM", () => {
    vi.setSystemTime(new Date("2026-08-06T10:00:00Z")); // Thursday
    expect(getScheduleRunAt("weekend")).toBe("2026-08-07T19:00:00.000Z");
  });

  test("'weekend' returns today at 7 PM on a Friday morning", () => {
    vi.setSystemTime(new Date("2026-08-07T10:00:00Z")); // Friday
    expect(getScheduleRunAt("weekend")).toBe("2026-08-07T19:00:00.000Z");
  });

  test("'weekend' rolls over to the next Friday on a Friday after 7 PM", () => {
    vi.setSystemTime(new Date("2026-08-07T20:00:00Z")); // Friday 8 PM
    expect(getScheduleRunAt("weekend")).toBe("2026-08-14T19:00:00.000Z");
  });

  test("'weekend' returns the next Friday on a Saturday", () => {
    vi.setSystemTime(new Date("2026-08-08T10:00:00Z")); // Saturday
    expect(getScheduleRunAt("weekend")).toBe("2026-08-14T19:00:00.000Z");
  });
});
