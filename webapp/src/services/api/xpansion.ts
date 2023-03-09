import { AxiosRequestConfig } from "axios";
import { MatrixType } from "../../common/types";
import {
  XpansionCandidate,
  XpansionSettings,
} from "../../components/App/Singlestudy/explore/Xpansion/types";
import client from "./client";

export const createXpansionConfiguration = async (
  uuid: string
): Promise<void> => {
  const res = await client.post(`/v1//studies/${uuid}/extensions/xpansion`);
  return res.data;
};

export const deleteXpansionConfiguration = async (
  uuid: string
): Promise<void> => {
  const res = await client.delete(`/v1/studies/${uuid}/extensions/xpansion`);
  return res.data;
};

export const getXpansionSettings = async (
  uuid: string
): Promise<XpansionSettings> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/settings`
  );
  return res.data;
};

export const xpansionConfigurationExist = async (
  uuid: string
): Promise<boolean> => {
  try {
    await client.get(`/v1/studies/${uuid}/extensions/xpansion/settings`);
    return Promise.resolve(true);
  } catch (e) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { status } = (e as any).response;
    if (status === 404) {
      return Promise.resolve(false);
    }
    throw e;
  }
};

export const updateXpansionSettings = async (
  uuid: string,
  settings: XpansionSettings
): Promise<XpansionSettings> => {
  const res = await client.put(
    `/v1/studies/${uuid}/extensions/xpansion/settings`,
    settings
  );
  return res.data;
};

export const getCandidate = async (
  uuid: string,
  name: string
): Promise<XpansionCandidate> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/candidates/${name}`
  );
  // Truc url encode
  return res.data;
};

export const getAllCandidates = async (
  uuid: string
): Promise<XpansionCandidate[]> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/candidates`
  );
  return res.data;
};

export const addCandidate = async (
  uuid: string,
  candidate: XpansionCandidate
): Promise<void> => {
  const res = await client.post(
    `/v1/studies/${uuid}/extensions/xpansion/candidates`,
    candidate
  );
  return res.data;
};

export const updateCandidate = async (
  uuid: string,
  name: string,
  data: XpansionCandidate
): Promise<XpansionCandidate> => {
  const res = await client.put(
    `/v1/studies/${uuid}/extensions/xpansion/candidates/${name}`,
    data
  );
  return res.data;
};

export const deleteCandidate = async (
  uuid: string,
  name: string
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/extensions/xpansion/candidates/${encodeURIComponent(
      name
    )}`
  );
  return res.data;
};

export const uploadFile = async (
  url: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<void> => {
  const options: AxiosRequestConfig = {};
  if (onProgress) {
    options.onUploadProgress = (progressEvent): void => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / (progressEvent.total || 1)
      );
      onProgress(percentCompleted);
    };
  }
  const formData = new FormData();
  formData.append("file", file);
  const restconfig = {
    ...options,
    headers: {
      "content-type": "multipart/form-data",
    },
  };
  const res = await client.post(url, formData, restconfig);
  return res.data;
};

export const addConstraints = async (
  uuid: string,
  file: File
): Promise<void> => {
  await uploadFile(
    `/v1/studies/${uuid}/extensions/xpansion/resources/constraints`,
    file
  );
};

export const deleteConstraints = async (
  uuid: string,
  filename: string
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/extensions/xpansion/resources/constraints/${encodeURIComponent(
      filename
    )}`
  );
  return res.data;
};

export const getConstraint = async (
  uuid: string,
  filename: string
): Promise<string> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/resources/constraints/${filename}`
  );
  return res.data;
};

export const getAllConstraints = async (
  uuid: string
): Promise<Array<string>> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/resources/constraints`
  );
  return res.data;
};

export const addWeight = async (uuid: string, file: File): Promise<void> => {
  await uploadFile(
    `/v1/studies/${uuid}/extensions/xpansion/resources/weights`,
    file
  );
};

export const deleteWeight = async (
  uuid: string,
  filename: string
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/extensions/xpansion/resources/weights/${encodeURIComponent(
      filename
    )}`
  );
  return res.data;
};

export const getWeight = async (
  uuid: string,
  filename: string
): Promise<string> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/resources/weights/${filename}`
  );
  return res.data;
};

export const getAllWeights = async (uuid: string): Promise<Array<string>> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/resources/weights`
  );
  return res.data;
};

export const addCapacity = async (uuid: string, file: File): Promise<void> => {
  await uploadFile(
    `/v1/studies/${uuid}/extensions/xpansion/resources/capacities`,
    file
  );
};

export const deleteCapacity = async (
  uuid: string,
  filename: string
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/extensions/xpansion/resources/capacities/${encodeURIComponent(
      filename
    )}`
  );
  return res.data;
};

export const getCapacity = async (
  uuid: string,
  filename: string
): Promise<MatrixType> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/resources/capacities/${filename}`
  );
  return res.data;
};

export const getAllCapacities = async (
  uuid: string
): Promise<Array<string>> => {
  const res = await client.get(
    `/v1/studies/${uuid}/extensions/xpansion/resources/capacities`
  );
  return res.data;
};

export default {};
