/**
 * Get parent paths of a given path.
 *
 * @example
 * getParentPaths("a/b/c/d"); // Returns: ["a", "a/b", "a/b/c"]
 *
 * @param path - The path from which to get the parent paths.
 * @returns The parent paths.
 */
export function getParentPaths(path: string) {
  return path
    .split("/")
    .slice(0, -1) // Remove the last item
    .map((_, index, arr) => arr.slice(0, index + 1).join("/"));
}
