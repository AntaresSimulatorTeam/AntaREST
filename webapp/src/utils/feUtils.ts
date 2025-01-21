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

import type { HTMLInputTypeAttribute } from "react";

export interface InputObject {
  value: unknown;
  checked?: boolean;
  type?: HTMLInputTypeAttribute;
  name?: string;
}

type Target = HTMLInputElement | InputObject;

export interface FakeChangeEventHandler {
  target: Target;
  type: "change";
}

export interface FakeBlurEventHandler {
  target: Target;
  type: "blur";
}

export function createFakeChangeEventHandler(target: Target): FakeChangeEventHandler {
  return {
    target,
    type: "change",
  };
}

export function createFakeBlurEventHandler(target: Target): FakeBlurEventHandler {
  return {
    target,
    type: "blur",
  };
}

export function createFakeInputElement(obj: InputObject): HTMLInputElement {
  const inputElement = document.createElement("input");
  inputElement.name = obj.name || "";
  inputElement.value = obj.value as string;

  return inputElement;
}
