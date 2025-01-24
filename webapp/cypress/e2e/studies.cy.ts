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

describe("Studies Page", () => {
  beforeEach(() => {
    cy.login().then(() => {
      cy.intercept(
        {
          method: "GET",
          url: "/v1/studies",
          headers: {
            Authorization: `Bearer ${Cypress.env("AUTH_TOKEN")}`,
          },
        },
        {
          statusCode: 200,
          body: [
            { id: "1", name: "Study 1", description: "First study" },
            { id: "2", name: "Study 2", description: "Second study" },
          ],
        },
      ).as("getStudies");

      cy.visit("/studies");
      cy.wait("@getStudies");
    });
  });

  it("should display the studies page correctly", () => {
    cy.findByRole("heading", { name: /studies/i }).should("exist");

    cy.findByRole("list", { name: /studies list/i }).within(() => {
      cy.findByText("Study 1").should("exist");
      cy.findByText("Study 2").should("exist");
    });
  });

  it("should handle loading state", () => {
    cy.intercept(
      {
        method: "GET",
        url: "/v1/studies",
        headers: {
          Authorization: `Bearer ${Cypress.env("AUTH_TOKEN")}`,
        },
      },
      (req) => {
        req.reply({
          delay: 1000,
          body: [],
        });
      },
    ).as("delayedStudies");
    cy.visit("/studies");
    cy.findByRole("status", { name: /loading/i }).should("exist");
  });

  it("should handle error state", () => {
    cy.intercept(
      {
        method: "GET",
        url: "/v1/studies",
        headers: {
          Authorization: `Bearer ${Cypress.env("AUTH_TOKEN")}`,
        },
      },
      {
        forceNetworkError: true,
      },
    ).as("errorStudies");

    cy.visit("/studies");
    cy.findByRole("alert", { name: /error/i }).should("contain", "Failed to load studies");
  });
});
