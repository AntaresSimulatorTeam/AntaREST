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

export interface QueryListItemBase {
  id: string;
  name: string;
}

export interface QueryListItemMetadata {
  isOptimistic?: boolean;
}

export type QueryListItem<T extends QueryListItemBase = QueryListItemBase> = T & {
  _metadata?: QueryListItemMetadata;
};

export type QueryList<T extends QueryListItemBase> = Array<QueryListItem<T>>;
