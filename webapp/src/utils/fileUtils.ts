/**
 * Triggers the download of a file with the given data and name.
 *
 * @param fileData - The data of the file to be downloaded.
 * @param fileName - The name of the file to be downloaded.
 */
export function downloadFile(fileData: BlobPart, fileName: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([fileData]));
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(link.href);
}
