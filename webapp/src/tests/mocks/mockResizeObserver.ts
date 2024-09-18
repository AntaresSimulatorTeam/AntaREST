/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

/**
 * This is a mock implementation of the global `ResizeObserver`.
 * ResizeObserver is a web API used to monitor changes in an element's size.
 * As Vitest runs in a Node environment where certain browser-specific APIs like ResizeObserver are not available,
 * we need to mock these APIs to prevent errors during testing and ensure that components relying on them can be tested.
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver/ResizeObserver
 */
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  // The `observe` method is responsible for starting the observation of size changes on the specified element.
  // We mock this method to simply track calls (since actual DOM measurements aren't possible in Jest or Vitest environments).
  observe: vi.fn(),

  // The `unobserve` method stops the observation of an element. It's essential for cleanup in real usage to avoid memory leaks,
  // but here it's just a mock to ensure we can verify calls to it during tests.
  unobserve: vi.fn(),

  // The `disconnect` method stops all observations by this instance of ResizeObserver.
  // This is used to clean up observers when a component unmounts. The mock helps to simulate and test these cleanup behaviors.
  disconnect: vi.fn(),
}));
