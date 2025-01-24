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
    // Mock API response for studies
    cy.intercept("GET", "/v1/studies", {
      statusCode: 200,
      body: [
        { id: "1", name: "Study 1", description: "First study" },
        { id: "2", name: "Study 2", description: "Second study" },
      ],
    }).as("getStudies");

    cy.visit("/studies");
  });

  it("should display the studies page correctly", () => {
    // Check page title
    cy.get("h1").should("contain", "Studies");

    // Check header elements
    cy.get("header").should("contain", "Global Studies");
    cy.get('button[aria-label="Filter"]').should("exist");

    // Check side navigation
    cy.get("nav").within(() => {
      cy.contains("All Studies").should("exist");
      cy.contains("Favorites").should("exist");
    });

    // Verify studies list
    cy.get('[data-testid="studies-list"]').within(() => {
      cy.contains("Study 1").should("exist");
      cy.contains("Study 2").should("exist");
    });
  });

  it("should handle loading state", () => {
    // Delay the API response to test loading state
    cy.intercept("GET", "/v1/studies", (req) => {
      req.reply({
        delay: 1000,
        body: [],
      });
    }).as("delayedStudies");

    cy.get('[data-testid="loading-spinner"]').should("exist");
  });

  it("should handle error state", () => {
    // Force API error
    cy.intercept("GET", "/v1/studies", {
      forceNetworkError: true,
    }).as("errorStudies");

    cy.contains("Failed to load studies").should("exist");
    cy.get("button").contains("Refresh").should("exist");
  });
});
