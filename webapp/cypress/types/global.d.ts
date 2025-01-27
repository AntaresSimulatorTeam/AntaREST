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

import { mount } from "cypress/react";
import type { TAppPages } from ".";

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Full authentication flow using API calls and Testing Library
       *
       * @example cy.login() // Uses env vars
       * @example cy.login('customUser', 'securePass')
       */
      login(username?: string, password?: string): Chainable<void>;

      /**
       * Navigate to a specific page in the application
       *
       * @example cy.navigateTo('studies')
       */
      navigateTo(page: TAppPages): Chainable<void>;

      /**
       * Mount component for testing
       *
       * @example cy.mount(<MyComponent />)
       */
      mount: typeof mount;
    }
  }
}
