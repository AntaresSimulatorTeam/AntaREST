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

import { uniqueArray } from "@/utils/zodUtils";
import type { EnumLike } from "node_modules/zod/v4/core/util.cjs";
import z from "zod";

////////////////////////////////////////////////////////////////
// Response Schemas
////////////////////////////////////////////////////////////////

export const tableModeTypeSchema = z.enum([
  "areas",
  "links",
  "thermals",
  "renewables",
  "st-storages",
  "binding-constraints",
  "st-storages-additional-constraints",
]);

const areaColumnsSchema = uniqueArray(
  z.enum([
    "nonDispatchPower",
    "dispatchHydroPower",
    "otherDispatchPower",
    "energyCostUnsupplied",
    "spreadUnsuppliedEnergyCost",
    "energyCostSpilled",
    "spreadSpilledEnergyCost",
    "filterSynthesis",
    "filterByYear",
    // Since v8.3
    "adequacyPatchMode",
  ]),
);

const linkColumnsSchema = uniqueArray(
  z.enum([
    "hurdlesCost",
    "loopFlow",
    "usePhaseShifter",
    "transmissionCapacities",
    "assetType",
    "linkStyle",
    "linkWidth",
    "comments",
    "displayComments",
    "filterSynthesis",
    "filterYearByYear",
  ]),
);

const thermalColumnsSchema = uniqueArray(
  z.enum([
    "group",
    "enabled",
    "unitCount",
    "nominalCapacity",
    "genTs",
    "minStablePower",
    "minUpTime",
    "minDownTime",
    "mustRun",
    "spinning",
    "volatilityForced",
    "volatilityPlanned",
    "lawForced",
    "lawPlanned",
    "marginalCost",
    "spreadCost",
    "fixedCost",
    "startupCost",
    "marketBidCost",
    "co2",
    // Since v8.6
    "nh3",
    "so2",
    "nox",
    "pm25",
    "pm5",
    "pm10",
    "nmvoc",
    "op1",
    "op2",
    "op3",
    "op4",
    "op5",
    // Since v8.7
    "costGeneration",
    "efficiency",
    "variableOMCost",
  ]),
);

const renewableColumnsSchema = uniqueArray(
  z.enum([
    // Since v8.1
    "group",
    "enabled",
    "tsInterpretation",
    "unitCount",
    "nominalCapacity",
  ]),
);

const stStorageColumnsSchema = uniqueArray(
  z.enum([
    // Since v8.6
    "group",
    "injectionNominalCapacity",
    "withdrawalNominalCapacity",
    "reservoirCapacity",
    "efficiency",
    "initialLevel",
    "initialLevelOptim",
    // Since v8.8
    "enabled",
    // Since v9.2
    "efficiencyWithdrawal",
    "penalizeVariationInjection",
    "penalizeVariationWithdrawal",
  ]),
);

const bindingConstraintColumnsSchema = uniqueArray(
  z.enum([
    "enabled",
    "timeStep",
    "operator",
    "comments",
    // Since v8.3
    "filterSynthesis",
    "filterYearByYear",
    // Since v8.7
    "group",
  ]),
);

const stStorageAdditionalConstraintColumnsSchema = uniqueArray(
  z.enum([
    // Since v9.2
    "variable",
    "operator",
    "enabled",
  ]),
);

function createTableModeSchemaForType<
  TType extends z.infer<typeof tableModeTypeSchema>,
  TEnum extends EnumLike,
>(type: TType, columnsSchema: z.ZodArray<z.ZodEnum<TEnum>>) {
  return (
    z
      .object({
        table_id: z.string(),
        table_name: z.string(),
        table_type: z.literal(type),
        table_columns: columnsSchema,
      })
      // Transform must be applied here, not on the outer discriminatedUnion,
      // to preserve narrowed type inference between `type` and `columns`.
      .transform((data) => ({
        id: data.table_id,
        name: data.table_name,
        type: data.table_type,
        columns: data.table_columns,
      }))
  );
}

function createTableModeCreationSchemaForType<
  TType extends z.infer<typeof tableModeTypeSchema>,
  TEnum extends EnumLike,
>(type: TType, columnsSchema: z.ZodArray<z.ZodEnum<TEnum>>) {
  return z
    .object({
      type: z.literal(type),
      name: z.string(),
      columns: columnsSchema,
    })
    .transform(({ name, type, columns }) => ({
      table_name: name,
      table_type: type,
      table_columns: columns,
    }));
}

function createTableModeUpdateSchemaForType<
  TType extends z.infer<typeof tableModeTypeSchema>,
  TEnum extends EnumLike,
>(type: TType, columnsSchema: z.ZodArray<z.ZodEnum<TEnum>>) {
  return z
    .object({
      type: z.literal(type),
      columns: columnsSchema,
    })
    .transform(({ type, columns }) => ({
      table_type: type,
      table_columns: columns,
    }));
}

export const tableModeSchema = z.discriminatedUnion("table_type", [
  createTableModeSchemaForType("areas", areaColumnsSchema),
  createTableModeSchemaForType("links", linkColumnsSchema),
  createTableModeSchemaForType("thermals", thermalColumnsSchema),
  createTableModeSchemaForType("renewables", renewableColumnsSchema),
  createTableModeSchemaForType("st-storages", stStorageColumnsSchema),
  createTableModeSchemaForType("binding-constraints", bindingConstraintColumnsSchema),
  createTableModeSchemaForType(
    "st-storages-additional-constraints",
    stStorageAdditionalConstraintColumnsSchema,
  ),
]);

export const tableModeCreationSchema = z.discriminatedUnion("type", [
  createTableModeCreationSchemaForType("areas", areaColumnsSchema),
  createTableModeCreationSchemaForType("links", linkColumnsSchema),
  createTableModeCreationSchemaForType("thermals", thermalColumnsSchema),
  createTableModeCreationSchemaForType("renewables", renewableColumnsSchema),
  createTableModeCreationSchemaForType("st-storages", stStorageColumnsSchema),
  createTableModeCreationSchemaForType("binding-constraints", bindingConstraintColumnsSchema),
  createTableModeCreationSchemaForType(
    "st-storages-additional-constraints",
    stStorageAdditionalConstraintColumnsSchema,
  ),
]);

export const tableModeUpdateSchema = z.discriminatedUnion("type", [
  createTableModeUpdateSchemaForType("areas", areaColumnsSchema),
  createTableModeUpdateSchemaForType("links", linkColumnsSchema),
  createTableModeUpdateSchemaForType("thermals", thermalColumnsSchema),
  createTableModeUpdateSchemaForType("renewables", renewableColumnsSchema),
  createTableModeUpdateSchemaForType("st-storages", stStorageColumnsSchema),
  createTableModeUpdateSchemaForType("binding-constraints", bindingConstraintColumnsSchema),
  createTableModeUpdateSchemaForType(
    "st-storages-additional-constraints",
    stStorageAdditionalConstraintColumnsSchema,
  ),
]);
