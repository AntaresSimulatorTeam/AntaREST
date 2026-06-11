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

// TODO: Remove this file when the v10 backend reserves endpoints are available.
// In-memory fake implementation of the reserves API, used while the backend
// doesn't support reserves yet (requires study version >= 10).

import type {
  CreateReserveParams,
  DeleteReservesParams,
  GetReserveParams,
  Reserve,
  ReserveGlobalParameters,
  ReservesAreaParams,
  UpdateReserveGlobalParametersParams,
  UpdateReserveParams,
} from "./types";

const FAKE_NETWORK_DELAY = 500;

const INITIAL_RESERVES: Reserve[] = [
  {
    id: "primary reserve",
    type: "up",
    failureCost: 10000,
    spillageCost: 0,
    referenceActivationDuration: 30,
    powerActivationRatio: 1,
    energyActivationRatio: 0.5,
  },
  {
    id: "secondary reserve",
    type: "up",
    failureCost: 8000,
    spillageCost: 100,
    referenceActivationDuration: 300,
    powerActivationRatio: 0.8,
    energyActivationRatio: 0.4,
  },
  {
    id: "tertiary reserve",
    type: "up",
    failureCost: 5000,
    spillageCost: 50,
    referenceActivationDuration: 900,
    powerActivationRatio: 0.6,
    energyActivationRatio: 0.3,
  },
  {
    id: "primary reserve down",
    type: "down",
    failureCost: 9000,
    spillageCost: 0,
    referenceActivationDuration: 30,
    powerActivationRatio: 1,
    energyActivationRatio: 0.5,
  },
  {
    id: "secondary reserve down",
    type: "down",
    failureCost: 7000,
    spillageCost: 200,
    referenceActivationDuration: 300,
    powerActivationRatio: 0.7,
    energyActivationRatio: 0.35,
  },
];

const INITIAL_GLOBAL_PARAMETERS: ReserveGlobalParameters = {
  referenceActivationDurationUp: 30,
  energyActivationRatioUp: 0.5,
  referenceActivationDurationDown: 30,
  energyActivationRatioDown: 0.5,
};

// Stores keyed by `${studyId}/${areaId}`
const reservesByArea = new Map<string, Reserve[]>();
const globalParametersByArea = new Map<string, ReserveGlobalParameters>();

function getAreaKey({ studyId, areaId }: ReservesAreaParams) {
  return `${studyId}/${areaId}`;
}

function getAreaReserves(params: ReservesAreaParams) {
  const key = getAreaKey(params);
  let reserves = reservesByArea.get(key);

  if (!reserves) {
    reserves = INITIAL_RESERVES.map((reserve) => ({ ...reserve }));
    reservesByArea.set(key, reserves);
  }

  return reserves;
}

function delay() {
  return new Promise((resolve) => setTimeout(resolve, FAKE_NETWORK_DELAY));
}

////////////////////////////////////////////////////////////////
// Fake API
////////////////////////////////////////////////////////////////

export async function getReserves(params: ReservesAreaParams): Promise<Reserve[]> {
  await delay();
  return getAreaReserves(params).map((reserve) => ({ ...reserve }));
}

export async function getReserve(params: GetReserveParams): Promise<Reserve> {
  await delay();
  const reserve = getAreaReserves(params).find((r) => r.id === params.reserveId);

  if (!reserve) {
    throw new Error(`Reserve "${params.reserveId}" not found`);
  }

  return { ...reserve };
}

export async function createReserve(params: CreateReserveParams): Promise<Reserve> {
  await delay();
  const { data } = params;
  const reserves = getAreaReserves(params);

  if (reserves.some((r) => r.id.toLowerCase() === data.id.toLowerCase())) {
    throw new Error(`Reserve "${data.id}" already exists`);
  }

  const newReserve: Reserve = {
    id: data.id,
    type: data.type,
    failureCost: data.failureCost ?? 0,
    spillageCost: data.spillageCost ?? 0,
    referenceActivationDuration: data.referenceActivationDuration ?? 0,
    powerActivationRatio: data.powerActivationRatio ?? 0,
    energyActivationRatio: data.energyActivationRatio ?? 0,
  };

  reserves.push(newReserve);

  return { ...newReserve };
}

export async function updateReserve(params: UpdateReserveParams): Promise<Reserve> {
  await delay();
  const reserves = getAreaReserves(params);
  const index = reserves.findIndex((r) => r.id === params.reserveId);

  if (index === -1) {
    throw new Error(`Reserve "${params.reserveId}" not found`);
  }

  reserves[index] = { ...reserves[index], ...params.data };

  return { ...reserves[index] };
}

export async function deleteReserves(params: DeleteReservesParams): Promise<void> {
  await delay();
  const key = getAreaKey(params);
  reservesByArea.set(
    key,
    getAreaReserves(params).filter((r) => !params.reserveIds.includes(r.id)),
  );
}

export async function getReserveGlobalParameters(
  params: ReservesAreaParams,
): Promise<ReserveGlobalParameters> {
  await delay();
  const parameters = globalParametersByArea.get(getAreaKey(params)) ?? INITIAL_GLOBAL_PARAMETERS;
  return { ...parameters };
}

export async function updateReserveGlobalParameters(
  params: UpdateReserveGlobalParametersParams,
): Promise<ReserveGlobalParameters> {
  await delay();
  const key = getAreaKey(params);
  const parameters = {
    ...(globalParametersByArea.get(key) ?? INITIAL_GLOBAL_PARAMETERS),
    ...params.data,
  };
  globalParametersByArea.set(key, parameters);
  return parameters;
}
