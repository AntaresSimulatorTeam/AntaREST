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

import client from "./client";
import type {
  CommandDTO,
  FileStudyTreeConfigDTO,
  StudyMetadata,
  StudyMetadataDTO,
  VariantTree,
} from "../../types/types";
import { convertStudyDtoToMetadata, convertVariantTreeDTO } from "../utils";
import type { FileDownloadTask } from "./downloads";
import type { TaskDTO } from "./tasks/types";

export const getVariantChildren = async (id: string): Promise<VariantTree> => {
  const res = await client.get(`/v1/studies/${id}/variants`);
  return convertVariantTreeDTO(res.data);
};

export const getVariantParents = async (id: string): Promise<StudyMetadata[]> => {
  const res = await client.get(`/v1/studies/${id}/parents`);
  return res.data.map((elm: StudyMetadataDTO) => convertStudyDtoToMetadata(elm.id, elm));
};

export const getDirectParent = async (id: string): Promise<StudyMetadata | undefined> => {
  const res = await client.get(`/v1/studies/${id}/parents?direct=true`);
  if (res.data) {
    return convertStudyDtoToMetadata(res.data.id, res.data);
  }
  return undefined;
};

export const createVariant = async (id: string, name: string): Promise<string> => {
  const res = await client.post(`/v1/studies/${id}/variants?name=${encodeURIComponent(name)}`);
  return res.data;
};

export const appendCommands = async (studyId: string, commands: CommandDTO[]): Promise<string> => {
  const res = await client.post(`/v1/studies/${studyId}/commands`, commands);
  return res.data;
};

export const appendCommand = async (studyId: string, command: CommandDTO): Promise<string> => {
  const res = await client.post(`/v1/studies/${studyId}/command`, command);
  return res.data;
};

export const moveCommand = async (
  studyId: string,
  commandId: string,
  index: number,
): Promise<void> => {
  const res = await client.put(
    `/v1/studies/${studyId}/commands/${commandId}/move?index=${encodeURIComponent(index)}`,
  );
  return res.data;
};

export const updateCommand = async (
  studyId: string,
  commandId: string,
  command: CommandDTO,
): Promise<void> => {
  const res = await client.put(`/v1/studies/${studyId}/commands/${commandId}`, command);
  return res.data;
};

export const replaceCommands = async (studyId: string, commands: CommandDTO[]): Promise<string> => {
  const res = await client.put(`/v1/studies/${studyId}/commands`, commands);
  return res.data;
};

export const deleteCommand = async (studyId: string, commandId: string): Promise<void> => {
  const res = await client.delete(`/v1/studies/${studyId}/commands/${commandId}`);
  return res.data;
};

export const deleteAllCommands = async (studyId: string): Promise<void> => {
  const res = await client.delete(`/v1/studies/${studyId}/commands`);
  return res.data;
};

export const getCommand = async (studyId: string, commandId: string): Promise<CommandDTO> => {
  const res = await client.get(`/v1/studies/${studyId}/commands/${commandId}`);
  return res.data;
};

export const getCommands = async (studyId: string): Promise<CommandDTO[]> => {
  const res = await client.get(`/v1/studies/${studyId}/commands`);
  return res.data;
};

export const exportCommandsMatrices = async (studyId: string): Promise<FileDownloadTask> => {
  const res = await client.get(`/v1/studies/${studyId}/commands/_matrices`);
  return res.data;
};

export const applyCommands = async (studyId: string, denormalize = false): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${studyId}/generate?denormalize=${denormalize}&from_scratch=true`,
  );
  return res.data;
};

export const getStudyTask = async (studyId: string): Promise<TaskDTO> => {
  const res = await client.get(`/v1/studies/${studyId}/task`);
  return res.data;
};

export const getTask = async (id: string, withLogs = false): Promise<TaskDTO> => {
  const res = await client.get(`/v1/tasks/${id}?with_logs=${withLogs}`);
  return res.data;
};

export const getStudySynthesis = async (studyId: string): Promise<FileStudyTreeConfigDTO> => {
  const res = await client.get(`/v1/studies/${studyId}/synthesis`);
  return res.data;
};

export default {};
