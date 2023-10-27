import { DependencyList } from "react";
import { useNavigate, To } from "react-router-dom";
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
 * A React hook for conditional navigation using react-router-dom.
 *
 * @function
 * @name useNavigateOnCondition
 *
 * @param {Object} options - Configuration options for the hook.
 * @param {DependencyList} options.deps - An array of dependencies that the effect will observe.
 * @param {To} options.to - The target location to navigate to, it could be a route as a string or a relative numeric location.
 * @param {function} [options.shouldNavigate] - An optional function that returns a boolean to determine whether navigation should take place.
 *
 * @example
 * - Basic usage
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
