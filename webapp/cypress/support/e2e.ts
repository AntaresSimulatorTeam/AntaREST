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

import { AppPages } from "@cypress/constants";
import "@testing-library/cypress/add-commands";

Cypress.Commands.add(
  "login",
  (username = Cypress.env("USERNAME"), password = Cypress.env("PASSWORD")) => {
    cy.session([username, password], () => {
      cy.request({
        method: "POST",
        url: "/v1/login",
        body: { username, password },
        headers: {
          "Content-Type": "application/json",
        },
      }).then(({ body }) => {
        // Store tokens in env vars
        Cypress.env("ACCESS_TOKEN", body.access_token);
        Cypress.env("REFRESH_TOKEN", body.refresh_token);
      });
    });

    // Verify successful login
    cy.visit("/");
    cy.findByRole("heading", { name: /antares web/i }).should("exist");
    cy.url().should("include", "/studies");
  },
);

Cypress.Commands.add("navigateTo", (page) => {
  const path = AppPages[page];

  cy.location("pathname").then((currentPath) => {
    if (currentPath !== path) {
      cy.visit(path);
    }
  });
});

// Global intercepts for common API calls
beforeEach(() => {
  cy.intercept("GET", "/v1/health", { statusCode: 200 }).as("healthCheck");
});
