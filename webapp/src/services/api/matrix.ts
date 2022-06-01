import { AxiosRequestConfig } from "axios";
import client from "./client";
import {
  MatrixDTO,
  MatrixDataSetDTO,
  MatrixInfoDTO,
  MatrixDataSetUpdateDTO,
  MatrixIndex,
} from "../../common/types";
import { FileDownloadTask } from "./downloads";
import { getConfig } from "../config";
import { MatrixEditDTO } from "../../components/singlestudy/explore/Modelization/Matrix/type";

export const getMatrixList = async (
  name = "",
  filterOwn = false
): Promise<Array<MatrixDataSetDTO>> => {
  const res = await client.get(
    `/v1/matrixdataset/_search?name=${encodeURI(name)}&filter_own=${filterOwn}`
  );
  return res.data;
};

export const getMatrix = async (id: string): Promise<MatrixDTO> => {
  const res = await client.get(`/v1/matrix/${id}`);
  return res.data;
};

export const getExportMatrixUrl = (matrixId: string): string =>
  `${
    getConfig().downloadHostUrl ||
    getConfig().baseUrl + getConfig().restEndpoint
  }/v1/matrix/${matrixId}/download`;

export const exportMatrixDataset = async (
  datasetId: string
): Promise<FileDownloadTask> => {
  const res = await client.get(`/v1/matrixdataset/${datasetId}/download`);
  return res.data;
};

export const createMatrixByImportation = async (
  file: File,
  json: boolean,
  onProgress?: (progress: number) => void
): Promise<Array<MatrixInfoDTO>> => {
  const options: AxiosRequestConfig = {};
  if (onProgress) {
    options.onUploadProgress = (progressEvent): void => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
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
  const res = await client.post(
    `/v1/matrix/_import?json=${json}`,
    formData,
    restconfig
  );
  return res.data;
};

export const createDataSet = async (
  metadata: MatrixDataSetUpdateDTO,
  matrices: Array<MatrixInfoDTO>
): Promise<MatrixDataSetDTO> => {
  const data = { metadata, matrices };
  const res = await client.post("/v1/matrixdataset", data);
  return res.data;
};

export const updateDataSet = async (
  id: string,
  metadata: MatrixDataSetUpdateDTO
): Promise<MatrixDataSetUpdateDTO> => {
  const res = await client.put(`/v1/matrixdataset/${id}/metadata`, metadata);
  return res.data;
};

export const deleteDataSet = async (id: string): Promise<void> => {
  const res = await client.delete(`/v1/matrixdataset/${id}`);
  return res.data;
};

export const editMatrix = async (
  sid: string,
  path: string,
  matrixEdit: MatrixEditDTO[]
): Promise<void> => {
  const res = await client.put(
    `/v1/studies/${sid}/matrix?path=${path}`,
    matrixEdit
  );
  return res.data;
};

export const getStudyMatrixIndex = async (
  sid: string
): Promise<MatrixIndex> => {
  const res = await client.get(`/v1/studies/${sid}/matrixindex`);
  return res.data;
};

export default {};
