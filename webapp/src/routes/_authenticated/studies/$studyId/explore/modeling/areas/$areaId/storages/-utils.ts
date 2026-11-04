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

import type { Storage } from "@/services/api/studies/areas/storages/types";
import * as RA from "ramda-adjunct";
import { adaptStorageToView } from "./-adapters";

export function getStoragesTotals(storages: Storage[]) {
  return storages.reduce(
    (acc, { withdrawalNominalCapacity, injectionNominalCapacity }) => {
      acc.totalWithdrawalNominalCapacity += withdrawalNominalCapacity;
      acc.totalInjectionNominalCapacity += injectionNominalCapacity;
      return acc;
    },
    {
      totalWithdrawalNominalCapacity: 0,
      totalInjectionNominalCapacity: 0,
    },
  );
}

export function convertRatioToPercentage<T extends Partial<Storage>>(storage: T): T {
  const values = { ...storage };

  // Convert to percentage ([0-1] -> [0-100])
  if (RA.isNumber(values.efficiency)) {
    values.efficiency *= 100;
  }
  if (RA.isNumber(values.initialLevel)) {
    values.initialLevel *= 100;
  }
  if (RA.isNumber(values.efficiencyWithdrawal)) {
    values.efficiencyWithdrawal *= 100;
  }

  return values;
}

export function convertPercentageToRatio(storage: Partial<Storage>): Partial<Storage> {
  const values = { ...storage };

  // Convert to ratio ([0-100] -> [0-1])
  if (RA.isNumber(values.efficiency)) {
    values.efficiency /= 100;
  }
  if (RA.isNumber(values.initialLevel)) {
    values.initialLevel /= 100;
  }
  if (RA.isNumber(values.efficiencyWithdrawal)) {
    values.efficiencyWithdrawal /= 100;
  }

  return values;
}

/**
 * Transforms a list of storages into enriched data for display.
 *
 * Totals are computed across all storages.
 *
 * Intended for use as the `select` option of a Tanstack Query hook.
 *
 * @see getStoragesTotals
 *
 * @param storages - The storages to select data for.
 * @returns An object containing the storages and their totals.
 */
export function selectStoragesData(storages: Storage[]) {
  return {
    formalizedStorages: storages.map(adaptStorageToView),
    totals: getStoragesTotals(storages),
  };
}
