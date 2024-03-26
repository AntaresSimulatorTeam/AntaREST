export function downloadFile(fileData: BlobPart, fileName: string) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([fileData]));
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(link.href);
}
