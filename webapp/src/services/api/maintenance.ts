/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

export const getMaintenanceMode = async (): Promise<boolean> => {
  const res = await client.get("/v1/core/maintenance");
  return res.data;
};

export const updateMaintenanceMode = async (data: boolean): Promise<void> => {
  const res = await client.post(`/v1/core/maintenance?maintenance=${data}`);
  return res.data;
};

export const getMessageInfo = async (): Promise<string> => {
  const res = await client.get("/v1/core/maintenance/message");
  return res.data;
};

export const updateMessageInfo = async (data: string): Promise<void> => {
  const res = await client.post("/v1/core/maintenance/message", data);
  return res.data;
};

export default {};
