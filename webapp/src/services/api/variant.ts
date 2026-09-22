/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import type { CommandDTO } from "../../types/types";
import client from "./client";
import { taskSchema } from "./tasks/schemas";

export const appendCommands = async (studyId: string, commands: CommandDTO[]): Promise<string> => {
  const res = await client.post(`/v1/studies/${studyId}/commands`, commands);
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

export const getCommands = async (studyId: string): Promise<CommandDTO[]> => {
  const res = await client.get(`/v1/studies/${studyId}/commands`);
  return res.data;
};

export const applyCommands = async (studyId: string): Promise<string> => {
  const res = await client.put(`/v1/studies/${studyId}/generate?from_scratch=true`);
  return res.data;
};

export async function getStudyTask(studyId: string) {
  const res = await client.get(`/v1/studies/${studyId}/task`);
  return taskSchema.parse(res.data);
}
