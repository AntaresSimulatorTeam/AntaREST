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

import { z } from "zod";
import { HYDRO_ASSET_ID, reservesCertificationsCodecs, reservesSymmetriesCodecs } from "../schemas";

const STORAGE_CERTIFICATION = { participationCost: 1, maxRelease: 2, maxStore: 3 };
const THERMAL_CERTIFICATION = {
  maxPower: 1,
  maxPowerOff: 2,
  participationCost: 3,
  participationCostOff: 4,
};

describe("reserves schemas", () => {
  describe("certifications codecs", () => {
    test("thermals and storages are asset-keyed on the wire: pass-through", () => {
      const thermals = { reserve_a: { cluster_1: THERMAL_CERTIFICATION } };
      const storages = { reserve_a: { storage_1: STORAGE_CERTIFICATION } };

      expect(reservesCertificationsCodecs.thermals.parse(thermals)).toEqual(thermals);
      expect(z.encode(reservesCertificationsCodecs.thermals, thermals)).toEqual(thermals);
      expect(reservesCertificationsCodecs.storages.parse(storages)).toEqual(storages);
      expect(z.encode(reservesCertificationsCodecs.storages, storages)).toEqual(storages);
    });

    test("rejects a certification of another production type", () => {
      expect(() =>
        reservesCertificationsCodecs.thermals.parse({
          reserve_a: { cluster_1: STORAGE_CERTIFICATION },
        }),
      ).toThrow();
    });

    test("hydro is keyed by reserve alone on the wire: wrapped under the hydro asset", () => {
      const wire = { reserve_a: STORAGE_CERTIFICATION, reserve_b: STORAGE_CERTIFICATION };

      const decoded = reservesCertificationsCodecs.hydro.parse(wire);

      expect(decoded).toEqual({
        reserve_a: { [HYDRO_ASSET_ID]: STORAGE_CERTIFICATION },
        reserve_b: { [HYDRO_ASSET_ID]: STORAGE_CERTIFICATION },
      });
      expect(z.encode(reservesCertificationsCodecs.hydro, decoded)).toEqual(wire);
    });

    test("hydro: a reserve without the hydro asset is dropped from the wire payload", () => {
      const encoded = z.encode(reservesCertificationsCodecs.hydro, {
        reserve_a: { [HYDRO_ASSET_ID]: STORAGE_CERTIFICATION },
        reserve_b: {},
      });

      expect(encoded).toEqual({ reserve_a: STORAGE_CERTIFICATION });
    });
  });

  describe("symmetries codecs", () => {
    test("thermals and storages are asset-keyed on the wire: pass-through", () => {
      const data = { cluster_1: [["reserve_a", "reserve_b"]] };

      expect(reservesSymmetriesCodecs.thermals.parse(data)).toEqual(data);
      expect(z.encode(reservesSymmetriesCodecs.storages, data)).toEqual(data);
    });

    test("hydro is a bare list on the wire: wrapped under the hydro asset", () => {
      const wire = [
        ["reserve_a", "reserve_b"],
        ["reserve_a", "reserve_c"],
      ];

      const decoded = reservesSymmetriesCodecs.hydro.parse(wire);

      expect(decoded).toEqual({ [HYDRO_ASSET_ID]: wire });
      expect(z.encode(reservesSymmetriesCodecs.hydro, decoded)).toEqual(wire);
    });

    test("hydro: no symmetries round-trips between [] and {}", () => {
      expect(reservesSymmetriesCodecs.hydro.parse([])).toEqual({});
      expect(z.encode(reservesSymmetriesCodecs.hydro, {})).toEqual([]);
    });
  });
});
