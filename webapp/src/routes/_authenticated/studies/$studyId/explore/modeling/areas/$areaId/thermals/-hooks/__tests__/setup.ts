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

vi.mock("@/services/api/client", () => ({ default: {} }));
vi.mock("@/i18n", () => ({ default: { t: (key: string) => key, language: "en" } }));
vi.mock("@/services/api/studies/areas/thermals");

const { t } = vi.hoisted(() => ({ t: (key: string) => key }));
vi.mock("react-i18next", () => ({ useTranslation: () => Object.assign([t], { t }) }));
