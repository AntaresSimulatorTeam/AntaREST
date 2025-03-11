/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import type { AxiosRequestConfig } from "axios";
import * as RA from "ramda-adjunct";
import client from "./client";
import type {
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
  LaunchOptions,
  StudyLayer,
} from "../../types/types";
import { convertStudyDtoToMetadata } from "../utils";
import type { FileDownloadTask } from "./downloads";
import type { StudyMapDistrict } from "../../redux/ducks/studyMaps";
import type { NonStudyFolderDTO } from "@/components/App/Studies/StudyTree/types";

interface Workspace {
  name: string;
}

const getStudiesRaw = async (): Promise<Record<string, StudyMetadataDTO>> => {
  const res = await client.get(`/v1/studies?exists=True`);
  return res.data;
};

export const getStudies = async (): Promise<StudyMetadata[]> => {
  const rawStudyList = await getStudiesRaw();
  return Object.keys(rawStudyList).map((sid) => {
    const study = rawStudyList[sid];
    return convertStudyDtoToMetadata(sid, study);
  });
};

export const getWorkspaces = async () => {
  const res = await client.get<Workspace[]>(`/v1/private/explorer/_list_workspaces`);
  return res.data.map((folder) => folder.name);
};

/**
 * Call the explorer API to get the list of folders in a workspace
 *
 * @param workspace - workspace name
 * @param folderPath - path starting from the workspace root (not including the workspace name)
 * @returns list of folders that are not studies, under the given path
 */
export const getFolders = async (workspace: string, folderPath: string) => {
  const res = await client.get<NonStudyFolderDTO[]>(
    `/v1/private/explorer/${workspace}/_list_dir?path=${encodeURIComponent(folderPath)}`,
  );
  return res.data;
};

export const getStudyVersions = async (): Promise<string[]> => {
  const res = await client.get("/v1/studies/_versions");
  return res.data;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const getStudyData = async <T = any>(sid: string, path = "", depth = 1): Promise<T> => {
  const res = await client.get(
    `/v1/studies/${sid}/raw?path=${encodeURIComponent(path)}&depth=${depth}`,
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

export const getStudyOutputs = async (sid: string): Promise<StudyOutput[]> => {
  const res = await client.get(`/v1/studies/${sid}/outputs`);
  return res.data;
};

export const getStudySynthesis = async (sid: string): Promise<FileStudyTreeConfigDTO> => {
  const res = await client.get(`/v1/studies/${sid}/synthesis`);
  return res.data;
};

export const downloadOutput = async (
  sid: string,
  output: string,
  data: StudyOutputDownloadDTO,
  jsonFormat = false,
  useTask = true,
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
    jsonFormat ? {} : restconfig,
  );
  return res.data;
};

export const createStudy = async (
  name: string,
  version: number,
  groups?: string[],
): Promise<string> => {
  const groupIds = groups && groups.length > 0 ? `&groups=${groups.join(",")}` : "";
  const res = await client.post(
    `/v1/studies?name=${encodeURIComponent(name)}&version=${version}${groupIds}`,
  );
  return res.data;
};

export const editStudy = async (
  data: object | string | boolean | number,
  sid: string,
  path = "",
  depth = 1,
): Promise<void> => {
  let formattedData: unknown = data;
  if (RA.isBoolean(data)) {
    formattedData = JSON.stringify(data);
  }
  const res = await client.post(
    `/v1/studies/${sid}/raw?path=${encodeURIComponent(path)}&depth=${depth}`,
    formattedData,
    {
      headers: {
        "content-type": "application/json",
      },
    },
  );
  return res.data;
};

export const copyStudy = async (sid: string, name: string, withOutputs: boolean): Promise<void> => {
  const res = await client.post(
    `/v1/studies/${sid}/copy?dest=${encodeURIComponent(name)}&with_outputs=${withOutputs}`,
  );
  return res.data;
};

export const moveStudy = async (studyId: string, folder: string) => {
  await client.put(`/v1/studies/${studyId}/move`, null, {
    params: { folder_dest: folder },
  });
};

export const archiveStudy = async (sid: string): Promise<void> => {
  await client.put(`/v1/studies/${sid}/archive`);
};

export const unarchiveStudy = async (sid: string): Promise<void> => {
  await client.put(`/v1/studies/${sid}/unarchive`);
};

export const upgradeStudy = async (studyId: string, targetVersion: string): Promise<void> => {
  await client.put(
    `/v1/studies/${studyId}/upgrade?target_version=${encodeURIComponent(targetVersion)}`,
  );
};

export const deleteStudy = async (sid: string, deleteAllChildren?: boolean): Promise<void> => {
  const res = await client.delete(`/v1/studies/${sid}?children=${deleteAllChildren || false}`);
  return res.data;
};

export const editComments = async (sid: string, newComments: string): Promise<void> => {
  const data = { comments: newComments };
  const res = await client.put(`/v1/studies/${sid}/comments`, data);
  return res.data;
};

export const exportStudy = async (sid: string, skipOutputs: boolean): Promise<FileDownloadTask> => {
  const res = await client.get(`/v1/studies/${sid}/export?no_output=${skipOutputs}`);
  return res.data;
};

export const exportOutput = async (sid: string, output: string): Promise<FileDownloadTask> => {
  const res = await client.get(`/v1/studies/${sid}/outputs/${output}/export`);
  return res.data;
};

export const importStudy = async (
  file: File,
  onProgress?: (progress: number) => void,
): Promise<StudyMetadata["id"]> => {
  const options: AxiosRequestConfig = {};
  if (onProgress) {
    options.onUploadProgress = (progressEvent): void => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / (progressEvent.total || 1),
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

export const launchStudy = async (
  sid: string,
  options: LaunchOptions = {},
  version: string | undefined = undefined,
): Promise<string> => {
  const versionArg = version ? `?version=${version}` : "";
  const res = await client.post(`/v1/launcher/run/${sid}${versionArg}`, options);
  return res.data;
};

interface LauncherMetrics {
  allocatedCpuRate: number;
  clusterLoadRate: number;
  nbQueuedJobs: number;
  status: string;
}

export const getLauncherVersions = async (): Promise<string[]> => {
  const res = await client.get("/v1/launcher/versions");
  return res.data;
};

export const getLauncherCores = async (): Promise<Record<string, number>> => {
  const res = await client.get("/v1/launcher/nbcores");
  return res.data;
};

/**
 * Time limit for SLURM jobs.
 * If a jobs exceed this time limit, SLURM kills the job and it is considered failed.
 *
 * @returns The min, defaultValue and max for the time limit in hours.
 */
export const getLauncherTimeLimit = async (): Promise<Record<string, number>> => {
  const res = await client.get("/v1/launcher/time-limit");
  return res.data;
};

export const getLauncherMetrics = async (): Promise<LauncherMetrics> => {
  const res = await client.get("/v1/launcher/load");
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
  launcherParams: JSON.parse(j.launcher_params),
  msg: j.msg,
  outputId: j.output_id,
  exitCode: j.exit_code,
});

export const getStudyJobs = (
  studyId?: string,
  filterOrphans = true,
  latest = false,
): Promise<LaunchJob[]> => {
  const queryParams = new URLSearchParams({
    filter_orphans: filterOrphans.toString(),
    ...(studyId && { study: studyId }),
    ...(latest && { latest: "100" }),
  });

  return client
    .get(`/v1/launcher/jobs?${queryParams}`)
    .then(({ data }) => data.map(mapLaunchJobDTO));
};

export const getStudyJobLog = async (
  jid: string,
  logType = "STDOUT",
): Promise<string | undefined> => {
  const res = await client.get(`/v1/launcher/jobs/${jid}/logs?log_type=${logType}`);
  return res.data;
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const downloadJobOutput = async (jobId: string): Promise<any> => {
  const res = await client.get(`/v1/launcher/jobs/${jobId}/output`);
  return res.data;
};

export const unarchiveOutput = async (studyId: string, outputId: string): Promise<string> => {
  const res = await client.post(
    `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/_unarchive`,
  );
  return res.data;
};

export const archiveOutput = async (studyId: string, outputId: string): Promise<string> => {
  const res = await client.post(
    `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/_archive`,
  );
  return res.data;
};

export const deleteOutput = async (studyId: string, outputId: string): Promise<void> => {
  await client.delete(`/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}`);
};

export const changeStudyOwner = async (
  studyId: string,
  newOwner: number,
): Promise<string | undefined> => {
  const res = await client.put(`/v1/studies/${studyId}/owner/${newOwner}`);
  return res.data;
};

export const deleteStudyGroup = async (studyId: string, groupId: string): Promise<void> => {
  const res = await client.delete(`/v1/studies/${studyId}/groups/${groupId}`);
  return res.data;
};

export const addStudyGroup = async (studyId: string, groupId: string): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}/groups/${groupId}`);
  return res.data;
};

export const changePublicMode = async (
  studyId: string,
  publicMode: StudyPublicMode,
): Promise<string | undefined> => {
  const res = await client.put(`/v1/studies/${studyId}/public_mode/${publicMode}`);
  return res.data;
};

export const renameStudy = async (studyId: string, name: string): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}`, {
    name,
  });
  return res.data;
};

export const updateStudyMetadata = async (
  studyId: string,
  data: StudyMetadataPatchDTO,
): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}`, data);
  return res.data;
};

export const scanFolder = async (folderPath: string, recursive = false) => {
  await client.post(
    `/v1/watcher/_scan?path=${encodeURIComponent(folderPath)}&recursive=${recursive}`,
  );
};

export const getStudyLayers = async (uuid: string): Promise<StudyLayer[]> => {
  const res = await client.get(`v1/studies/${uuid}/layers`);
  return res.data;
};

export async function createStudyLayer(
  studyId: StudyMetadata["id"],
  layerName: StudyLayer["name"],
): Promise<StudyLayer["id"]> {
  const res = await client.post(
    `v1/studies/${studyId}/layers?name=${encodeURIComponent(layerName)}`,
  );
  return res.data;
}

export async function updateStudyLayer(
  studyId: StudyMetadata["id"],
  layerId: StudyLayer["id"],
  layerName: StudyLayer["name"],
  areas?: StudyLayer["areas"],
): Promise<void> {
  await client.put(
    `v1/studies/${studyId}/layers/${layerId}?name=${encodeURIComponent(layerName)}`,
    areas,
  );
}

export async function deleteStudyLayer(
  studyId: StudyMetadata["id"],
  layerId: StudyLayer["id"],
): Promise<void> {
  await client.delete(`v1/studies/${studyId}/layers/${layerId}`);
}

export async function getStudyDistricts(studyId: StudyMetadata["id"]): Promise<StudyMapDistrict[]> {
  return (await client.get(`v1/studies/${studyId}/districts`)).data;
}

export async function createStudyDistrict(
  studyId: StudyMetadata["id"],
  districtName: StudyMapDistrict["name"],
  output: StudyMapDistrict["output"],
  comments: StudyMapDistrict["comments"],
): Promise<StudyMapDistrict> {
  return (
    await client.post(`v1/studies/${studyId}/districts`, {
      name: districtName,
      output,
      areas: [],
      comments,
    })
  ).data;
}

export async function updateStudyDistrict(
  studyId: StudyMetadata["id"],
  districtId: StudyMapDistrict["id"],
  output: StudyMapDistrict["output"],
  comments: StudyMapDistrict["comments"],
  areas?: StudyMapDistrict["areas"],
): Promise<void> {
  await client.put(`v1/studies/${studyId}/districts/${districtId}`, {
    output,
    comments,
    areas: areas || [],
  });
}

export async function deleteStudyDistrict(
  studyId: StudyMetadata["id"],
  districtId: StudyMapDistrict["id"],
): Promise<void> {
  await client.delete(`v1/studies/${studyId}/districts/${districtId}`);
}

export async function getStudyDiskUsage(studyId: StudyMetadata["id"]): Promise<number> {
  return (await client.get(`v1/studies/${studyId}/disk-usage`)).data;
}
