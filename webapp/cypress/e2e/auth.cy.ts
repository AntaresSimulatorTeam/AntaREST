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

describe("Authentication Flow", () => {
  describe("Login Page", () => {
    beforeEach(() => {
      cy.visit("/");
    });

    it("should not allow submit when form is empty", () => {
      cy.findByRole("button", { name: /connexion/i }).should("be.disabled");
    });

    it("should show error when using invalid credentials", () => {
      // Fill form with invalid credentials
      cy.findByLabelText(/nni/i).type("invalid_user");
      // TODO: fix the accessibility issue, and replace the css selector by "cy-data" or use testing lib API.
      cy.get('input[name="password"]').type("invalid_password");

      // Submit wrong user
      cy.findByRole("button", { name: /connexion/i })
        .should("be.enabled")
        .click();

      // Verify the login attempt fails
      // TODO: move css selector to "cy-data" or testing lib API.
      cy.get(".notistack-SnackbarContainer").within(() => {
        cy.findByText("Error while submitting").should("exist");
        // TODO: assertions below fail because of accessibility lack
        //cy.findByText("Status: 401").should("exist");
        //cy.findByText("Exception: HTTPException").should("exist");
        //cy.findByText("Description: Bad username or password").should("exist");
      });
    });
  });

  describe("Successful Authentication", () => {
    it("should store tokens for subsequent tests", () => {
      // Call login command with authenticated user
      cy.visit("/");
      cy.findByLabelText(/nni/i).type("admin");
      // TODO: move css selector to "cy-data" or testing lib API.
      cy.get('input[name="password"]').type("admin");
      cy.findByRole("button", { name: /connexion/i })
        .should("be.enabled")
        .click();

      cy.login();

      // Verify tokens are stored
      cy.wrap(Cypress.env("ACCESS_TOKEN")).should("be.a", "string");
      cy.wrap(Cypress.env("REFRESH_TOKEN")).should("be.a", "string");
    });
  });
});
