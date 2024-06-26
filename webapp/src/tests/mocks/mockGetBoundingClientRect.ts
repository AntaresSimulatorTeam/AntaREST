/**
 * Mocks the `getBoundingClientRect` method of the Element prototype.
 *
 * This utility function overrides the default `getBoundingClientRect` method
 * to return predetermined values. This is particularly useful in test environments
 * where the dimensions and positioning of elements cannot be accurately measured
 * as they would be in a fully rendered browser environment. By mocking these values,
 * tests can assert layout and dimension-related properties in a controlled and
 * predictable manner.
 *
 * Usage:
 * This mock should be set up in the setup phase of your tests, typically in a
 * `beforeEach` block, to ensure that every test runs with the same initial conditions.
 * Remember to restore or reset the original function after your tests to avoid
 * side effects, especially if other tests depend on the original behavior.
 *
 * @example
 * describe('Your Test Suite', () => {
 *   beforeEach(() => {
 *     mockGetBoundingClientRect();
 *   });
 *
 *   afterEach(() => {
 *     vi.restoreAllMocks();
 *   });
 *
 *   test('your test', () => {
 *     // your test code here
 *   });
 * });
 *
 * The mock is implemented by replacing `Element.prototype.getBoundingClientRect`
 * with a custom function that returns fixed dimensions:
 * - `width`: Calculated from the computed style of the element.
 * - `height`: Calculated from the computed style of the element.
 * - `top`: Always 0, simulating the element's position relative to the viewport.
 * - `left`: Always 0, simulating the element's position relative to the viewport.
 * - `bottom`: Calculated as the height, simulating the element's lower boundary relative to the viewport.
 * - `right`: Calculated as the width, simulating the element's right boundary relative to the viewport.
 * - `x`: Always 0, representing the x-coordinate of the element's bounding box.
 * - `y`: Always 0, representing the y-coordinate of the element's bounding box.
 * - `toJSON`: A function that returns an object representation of the bounding box.
 *
 * Note that the computed dimensions are based on the element's computed style at the time
 * of the function call, so tests should ensure that relevant styles are appropriately set
 * or mocked to reflect expected values.
 * @see https://developer.mozilla.org/fr/docs/Web/API/Element/getBoundingClientRect
 */
export const mockGetBoundingClientRect = () => {
  Element.prototype.getBoundingClientRect = vi.fn(function (this: Element) {
    const { width, height } = window.getComputedStyle(this);
    const rectWidth = parseInt(width, 10);
    const rectHeight = parseInt(height, 10);

    return {
      width: rectWidth,
      height: rectHeight,
      top: 0,
      left: 0,
      bottom: rectHeight,
      right: rectWidth,
      x: 0,
      y: 0,
      toJSON: () => ({
        width: rectWidth,
        height: rectHeight,
        top: 0,
        left: 0,
        bottom: rectHeight,
        right: rectWidth,
        x: 0,
        y: 0,
      }),
    };
  });
};
