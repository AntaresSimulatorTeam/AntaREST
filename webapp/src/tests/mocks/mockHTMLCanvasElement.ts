/**
 * Creates a mock for the HTML Canvas API in a testing environment.
 *
 * This function addresses the problem of testing components that rely on the
 * Canvas API in a Node.js environment, where the DOM and Canvas are not natively
 * available. Specifically, it solves issues related to testing components that
 * use libraries like @glideapps/glide-data-grid, which depend on canvas functionality.
 *
 * The mock provides stub implementations for commonly used CanvasRenderingContext2D
 * methods, allowing tests to run without throwing "not implemented" errors that
 * would typically occur when canvas methods are called in a non-browser environment.
 *
 * @returns An object containing the mocked context and getContext function.
 */
export const mockHTMLCanvasElement = () => {
  /**
   * A partial mock of CanvasRenderingContext2D.
   * Only the most commonly used methods are mocked to keep the implementation lean.
   * Additional methods can be added here as needed.
   */
  const contextMock: Partial<CanvasRenderingContext2D> = {
    measureText: vi.fn().mockReturnValue({
      width: 0,
      actualBoundingBoxAscent: 0,
      actualBoundingBoxDescent: 0,
      actualBoundingBoxLeft: 0,
      actualBoundingBoxRight: 0,
      fontBoundingBoxAscent: 0,
      fontBoundingBoxDescent: 0,
    }),
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    getImageData: vi
      .fn()
      .mockReturnValue({ data: new Uint8ClampedArray(), width: 0, height: 0 }),
    save: vi.fn(),
    fillText: vi.fn(),
    restore: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    closePath: vi.fn(),
    translate: vi.fn(),
    scale: vi.fn(),
    rotate: vi.fn(),
    arc: vi.fn(),
    rect: vi.fn(),
  };

  const getContextMock = vi.fn().mockReturnValue(contextMock);

  // Override the getContext method on the HTMLCanvasElement prototype
  window.HTMLCanvasElement.prototype.getContext = getContextMock;

  return { contextMock, getContextMock };
};
