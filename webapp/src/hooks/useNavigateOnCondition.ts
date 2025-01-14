/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import type { DependencyList } from "react";
import { useNavigate, type To } from "react-router-dom";
import { useUpdateEffect } from "react-use";

interface UseNavigateOnConditionOptions {
  /**
   * Dependencies that the effect should observe. Navigation will be triggered
   * based on changes to these dependencies and the result of shouldNavigate function.
   */
  deps: DependencyList;

  /**
   * A target location for navigation. It could be a route as string or a relative
   * numeric location.
   */
  to: To;

  /**
   * Function to determine whether to execute the navigation.
   * Defaults to true.
   */
  shouldNavigate?: () => boolean;
}

/**
 * A React hook for conditional navigation using react-router-dom. This hook allows for navigating to a different route
 * based on custom logic encapsulated in a `shouldNavigate` function. It observes specified dependencies and triggers navigation
 * when they change if the conditions defined in `shouldNavigate` are met.
 *
 * @param options - Configuration options for the hook.
 * @param options.deps - An array of dependencies that the effect will observe.
 * @param options.to - The target location to navigate to, which can be a route as a string or a relative numeric location.
 * @param options.shouldNavigate - An optional function that returns a boolean to determine whether navigation should take place. Defaults to a function that always returns true.
 *
 * @example
 * Basic usage
 * useNavigateOnCondition({
 *   deps: [someDependency],
 *   to: '/some-route',
 *   shouldNavigate: () => Boolean(someDependency),
 * });
 */

function useNavigateOnCondition({
  deps,
  to,
  shouldNavigate = (): boolean => true,
}: UseNavigateOnConditionOptions): void {
  const navigate = useNavigate();

  useUpdateEffect(() => {
    if (shouldNavigate()) {
      navigate(to);
    }
  }, [navigate, ...deps]);
}

export default useNavigateOnCondition;
