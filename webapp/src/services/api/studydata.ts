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

import {
  bindingConstraintModelAdapter,
  type BindingConstraint,
} from "@/routes/-App/Singlestudy/explore/Modelization/BindingConstraints/BindingConstView/utils";
import type { StudyMapNode } from "../../redux/ducks/studyMaps";
import type { AreaUIUpdatePayload, UpdateAreaUi } from "../../types/types";
import client from "./client";

export const createArea = async (uuid: string, name: string): Promise<StudyMapNode> => {
  const res = await client.post(`/v1/studies/${uuid}/areas`, {
    name,
    type: "AREA",
  });
  return res.data;
};

export const updateAreaUI = async (
  uuid: string,
  areaId: string,
  layerId: string,
  areaUi: UpdateAreaUi,
): Promise<string> => {
  const payload: AreaUIUpdatePayload = {
    x: areaUi.x,
    y: areaUi.y,
    color_rgb: areaUi.color_rgb,
  };
  const res = await client.put(`/v1/studies/${uuid}/areas/${areaId}/ui?layer=${layerId}`, payload);
  return res.data;
};

export const deleteArea = async (uuid: string, areaId: string): Promise<string> => {
  const res = await client.delete(`/v1/studies/${uuid}/areas/${areaId}`);
  return res.data;
};

export const getBindingConstraint = async (
  studyId: string,
  constraintId: string,
): Promise<BindingConstraint> => {
  const res = await client.get(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(constraintId)}`,
  );

  return bindingConstraintModelAdapter(res.data);
};

export const getBindingConstraintList = async (studyId: string): Promise<BindingConstraint[]> => {
  const res = await client.get(`/v1/studies/${studyId}/bindingconstraints`);
  return res.data;
};

export const updateBindingConstraint = async (
  studyId: string,
  constraintId: string,
  data: Omit<BindingConstraint, "id" | "name">,
): Promise<BindingConstraint> => {
  const adaptedData = bindingConstraintModelAdapter(data);

  const res = await client.put(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(constraintId)}`,
    adaptedData,
  );
  return res.data;
};

export const createBindingConstraint = async (
  studyId: string,
  data: Partial<BindingConstraint>,
): Promise<BindingConstraint> => {
  const res = await client.post(`/v1/studies/${studyId}/bindingconstraints`, data);
  return res.data;
};

export const duplicateBindingConstraint = async (
  studyId: string,
  constraintId: string,
  newConstraintName: string,
): Promise<BindingConstraint> => {
  const res = await client.post(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(constraintId)}`,
    null,
    {
      params: { new_constraint_name: newConstraintName },
    },
  );
  return res.data;
};

export const deleteBindingConstraint = async (
  studyId: string,
  constraintId: string,
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(constraintId)}`,
  );
  return res.data;
};
