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

import { AssetType, LinkStyle } from "@/services/api/studies/links/constants";
import type { Link } from "@/services/api/studies/links/types";

type LinkUI = Pick<Link, "assetType" | "linkWidth" | "linkStyle" | "colorr" | "colorb" | "colorg">;

export function getLinkUI(assetType: Link["assetType"]): LinkUI {
  switch (assetType) {
    case AssetType.AC:
      return {
        assetType,
        linkStyle: LinkStyle.Plain,
        linkWidth: 1,
        colorr: 112,
        colorg: 112,
        colorb: 112,
      };
    case AssetType.DC:
      return {
        assetType,
        linkStyle: LinkStyle.Dash,
        linkWidth: 2,
        colorr: 0,
        colorg: 255,
        colorb: 0,
      };
    case AssetType.Gaz:
      return {
        assetType,
        linkStyle: LinkStyle.Plain,
        linkWidth: 3,
        colorr: 0,
        colorg: 128,
        colorb: 255,
      };
    case AssetType.Virt:
      return {
        assetType,
        linkStyle: LinkStyle.DotDash,
        linkWidth: 2,
        colorr: 255,
        colorg: 0,
        colorb: 128,
      };
  }

  return {
    assetType: AssetType.Other,
    linkStyle: LinkStyle.Dot,
    linkWidth: 2,
    colorr: 255,
    colorg: 128,
    colorb: 0,
  };
}
