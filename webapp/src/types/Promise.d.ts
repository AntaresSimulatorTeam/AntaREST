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

// Allow changing the type of the parameter of `onrejected` callback from `any` to `unknown`
// https://github.com/microsoft/TypeScript/issues/45602#issuecomment-2573793430
interface Promise<T> {
  then<TFul, TRej = never>(
    onfulfilled?: ((value: T) => TFul | PromiseLike<TFul>) | null,
    onrejected?: ((reason: unknown) => TRej | PromiseLike<TRej>) | null,
  ): Promise<TFul | TRej>;

  catch<TRej = never>(
    onrejected?: ((reason: unknown) => TRej | PromiseLike<TRej>) | null,
  ): Promise<T | TRej>;
}
