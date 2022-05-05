import client from "./client";

export const getFileData = async (fileUrl: string): Promise<string> => {
  const res = await client.get(fileUrl);
  return res.data;
};

export default {};
