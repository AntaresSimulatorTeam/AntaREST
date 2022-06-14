import { AxiosRequestConfig } from "axios";
import { isBoolean, trimCharsStart } from "ramda-adjunct";
import client from "./client";
import {
  FileStudyTreeConfigDTO,
  LaunchJob,
  MatrixAggregationResult,
  StudyOutputDownloadDTO,
  StudyMetadata,
  StudyMetadataDTO,
  StudyOutput,
  StudyPublicMode,
  AreasConfig,
  LaunchJobDTO,
  StudyMetadataPatchDTO,
} from "../../common/types";
import { getConfig } from "../config";
import { convertStudyDtoToMetadata } from "../utils";
import { FileDownloadTask } from "./downloads";

const getStudiesRaw = async (): Promise<{
  [sid: string]: StudyMetadataDTO;
}> => {
  const res = await client.get(`/v1/studies`);
  return res.data;
};

export const getStudies = async (): Promise<StudyMetadata[]> => {
  const rawStudyList = await getStudiesRaw();
  return Object.keys(rawStudyList).map((sid) => {
    const study = rawStudyList[sid];
    return convertStudyDtoToMetadata(sid, study);
  });
};

export const getStudyVersions = async (): Promise<Array<string>> => {
  const res = await client.get("/v1/studies/_versions");
  return res.data;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const getStudyData = async <T = any>(
  sid: string,
  path = "",
  depth = 1
): Promise<T> => {
  const res = await client.get(
    `/v1/studies/${sid}/raw?path=${encodeURIComponent(path)}&depth=${depth}`
  );
  return res.data;
};

export const getComments = async (sid: string): Promise<string> => {
  const res = await client.get(`/v1/studies/${sid}/comments`);
  return res.data;
};

export const getAreaPositions = async (uuid: string): Promise<AreasConfig> => {
  const res = await client.get(`v1/studies/${uuid}/areas?ui=true`);
  return res.data;
};

export const getStudyMetadata = async (sid: string): Promise<StudyMetadata> => {
  const res = await client.get(`/v1/studies/${sid}`);
  return convertStudyDtoToMetadata(sid, res.data);
};

export const getStudyOutputs = async (
  sid: string
): Promise<Array<StudyOutput>> => {
  const res = await client.get(`/v1/studies/${sid}/outputs`);
  return res.data;
};

export const getStudySynthesis = async (
  sid: string
): Promise<FileStudyTreeConfigDTO> => {
  const res = await client.get(`/v1/studies/${sid}/synthesis`);
  return res.data;
};

export const downloadOutput = async (
  sid: string,
  output: string,
  data: StudyOutputDownloadDTO,
  jsonFormat = false,
  useTask = true
): Promise<FileDownloadTask | MatrixAggregationResult> => {
  const restconfig = {
    headers: {
      Accept: "application/zip",
      responseType: "blob",
    },
  };
  const res = await client.post(
    `/v1/studies/${sid}/outputs/${output}/download?use_task=${useTask}`,
    data,
    jsonFormat ? {} : restconfig
  );
  return res.data;
};

export const createStudy = async (
  name: string,
  version: number,
  groups?: Array<string>
): Promise<string> => {
  const groupIds =
    groups && groups.length > 0 ? `&groups=${groups.join(",")}` : "";
  const res = await client.post(
    `/v1/studies?name=${encodeURIComponent(name)}&version=${version}${groupIds}`
  );
  return res.data;
};

export const editStudy = async (
  data: object,
  sid: string,
  path = "",
  depth = 1
): Promise<void> => {
  let formattedData: unknown = data;
  if (isBoolean(data)) {
    formattedData = JSON.stringify(data);
  }
  const res = await client.post(
    `/v1/studies/${sid}/raw?path=${encodeURIComponent(path)}&depth=${depth}`,
    formattedData
  );
  return res.data;
};

export const copyStudy = async (
  sid: string,
  name: string,
  withOutputs: boolean
): Promise<void> => {
  const res = await client.post(
    `/v1/studies/${sid}/copy?dest=${encodeURIComponent(
      name
    )}&with_outputs=${withOutputs}`
  );
  return res.data;
};

export const moveStudy = async (sid: string, folder: string): Promise<void> => {
  const folderWithId = trimCharsStart("/", `${folder.trim()}/${sid}`);
  await client.put(
    `/v1/studies/${sid}/move?folder_dest=${encodeURIComponent(folderWithId)}`
  );
};

export const archiveStudy = async (sid: string): Promise<void> => {
  await client.put(`/v1/studies/${sid}/archive`);
};

export const unarchiveStudy = async (sid: string): Promise<void> => {
  await client.put(`/v1/studies/${sid}/unarchive`);
};

export const deleteStudy = async (sid: string): Promise<void> => {
  const res = await client.delete(`/v1/studies/${sid}`);
  return res.data;
};

export const editComments = async (
  sid: string,
  newComments: string
): Promise<void> => {
  const data = { comments: newComments };
  const res = await client.put(`/v1/studies/${sid}/comments`, data);
  return res.data;
};

export const exportStudy = async (
  sid: string,
  skipOutputs: boolean
): Promise<FileDownloadTask> => {
  const res = await client.get(
    `/v1/studies/${sid}/export?no_output=${skipOutputs}`
  );
  return res.data;
};

export const getExportUrl = (sid: string, skipOutputs = false): string =>
  `${
    getConfig().downloadHostUrl ||
    getConfig().baseUrl + getConfig().restEndpoint
  }/v1/studies/${sid}/export?no_output=${skipOutputs}`;

export const exportOuput = async (
  sid: string,
  output: string
): Promise<FileDownloadTask> => {
  const res = await client.get(`/v1/studies/${sid}/outputs/${output}/export`);
  return res.data;
};

export const importStudy = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<StudyMetadata["id"]> => {
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
  formData.append("study", file);
  const restconfig = {
    ...options,
    headers: {
      "content-type": "multipart/form-data",
    },
  };
  const res = await client.post("/v1/studies/_import", formData, restconfig);
  return res.data;
};

export const importFile = async (
  file: File,
  study: string,
  path: string,
  onProgress?: (progress: number) => void
): Promise<string> => {
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
  const res = await client.put(
    `/v1/studies/${study}/raw?path=${encodeURIComponent(path)}`,
    formData,
    restconfig
  );
  return res.data;
};

export interface LaunchOptions {
  xpansion?: boolean;
  // eslint-disable-next-line camelcase
  xpansion_r_version?: boolean;
  // eslint-disable-next-line camelcase
  nb_cpu?: number;
  // eslint-disable-next-line camelcase
  time_limit?: number;
  // eslint-disable-next-line camelcase
  post_processing?: boolean;
  // eslint-disable-next-line camelcase
  adequacy_patch?: object;
  // eslint-disable-next-line camelcase
  output_suffix?: string;
  // eslint-disable-next-line camelcase
  archive_output?: boolean;
  // eslint-disable-next-line camelcase
  other_options?: string;
}

export const launchStudy = async (
  sid: string,
  options: LaunchOptions = {},
  version: string | undefined = undefined
): Promise<string> => {
  const versionArg = version ? `?version=${version}` : "";
  const res = await client.post(
    `/v1/launcher/run/${sid}${versionArg}`,
    options
  );
  return res.data;
};

export const killStudy = async (jid: string): Promise<string> => {
  const res = await client.post(`/v1/launcher/jobs/${jid}/kill`);
  return res.data;
};

export const mapLaunchJobDTO = (j: LaunchJobDTO): LaunchJob => ({
  id: j.id,
  studyId: j.study_id,
  status: j.status,
  creationDate: j.creation_date,
  completionDate: j.completion_date,
  msg: j.msg,
  outputId: j.output_id,
  exitCode: j.exit_code,
});

export const getStudyJobs = async (
  sid?: string,
  filterOrphans = true,
  latest = false
): Promise<LaunchJob[]> => {
  let query = sid
    ? `?study=${sid}&filter_orphans=${filterOrphans}`
    : `?filter_orphans=${filterOrphans}`;
  if (latest) {
    query += "&latest=100";
  }
  const res = await client.get(`/v1/launcher/jobs${query}`);
  const data = await res.data;
  return data.map(mapLaunchJobDTO);
};

export const getStudyJobLog = async (
  jid: string,
  logType = "STDOUT"
): Promise<string | undefined> => {
  const res = await client.get(
    `/v1/launcher/jobs/${jid}/logs?log_type=${logType}`
  );
  return res.data;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const downloadJobOutput = async (jobId: string): Promise<any> => {
  const res = await client.get(`/v1/launcher/jobs/${jobId}/output`);
  return res.data;
};

export const changeStudyOwner = async (
  studyId: string,
  newOwner: number
): Promise<string | undefined> => {
  const res = await client.put(`/v1/studies/${studyId}/owner/${newOwner}`);
  return res.data;
};

export const deleteStudyGroup = async (
  studyId: string,
  groupId: string
): Promise<void> => {
  const res = await client.delete(`/v1/studies/${studyId}/groups/${groupId}`);
  return res.data;
};

export const addStudyGroup = async (
  studyId: string,
  groupId: string
): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}/groups/${groupId}`);
  return res.data;
};

export const changePublicMode = async (
  studyId: string,
  publicMode: StudyPublicMode
): Promise<string | undefined> => {
  const res = await client.put(
    `/v1/studies/${studyId}/public_mode/${publicMode}`
  );
  return res.data;
};

export const renameStudy = async (
  studyId: string,
  name: string
): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}`, {
    name,
  });
  return res.data;
};

export const updateStudyMetadata = async (
  studyId: string,
  data: StudyMetadataPatchDTO
): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}`, data);
  return res.data;
};

export const scanFolder = async (folderPath: string): Promise<void> => {
  await client.post(`/v1/watcher/_scan?path=${encodeURIComponent(folderPath)}`);
};

export default {};
