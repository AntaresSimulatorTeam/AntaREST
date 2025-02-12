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

import globals from "globals";
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import reactHookPlugin from "eslint-plugin-react-hooks";
import jsdocPlugin from "eslint-plugin-jsdoc";
import prettierPluginRecommended from "eslint-plugin-prettier/recommended";
import licenseHeaderPlugin from "eslint-plugin-license-header";
import reactRefreshPlugin from "eslint-plugin-react-refresh";
import cypressPlugin from "eslint-plugin-cypress/flat";

export default [
  // Must be defined here to be applied to all configurations.
  // cf. https://github.com/eslint/eslint/discussions/18304
  {
    ignores: ["dist/*", "license-header.js"],
  },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  ...tseslint.configs.stylistic,
  {
    ...reactPlugin.configs.flat.recommended,
    settings: {
      react: {
        version: "detect",
      },
    },
  },
  reactPlugin.configs.flat["jsx-runtime"],
  jsdocPlugin.configs["flat/recommended-typescript"],
  cypressPlugin.configs.recommended,
  prettierPluginRecommended, // Must be the last one
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2022,
        ...globals.cypress,
      },
    },
    plugins: {
      "license-header": licenseHeaderPlugin,
      "react-hooks": reactHookPlugin,
      "react-refresh": reactRefreshPlugin,
      cypress: cypressPlugin,
    },
    rules: {
      ...reactHookPlugin.configs.recommended.rules,
      "@typescript-eslint/array-type": ["error", { default: "array-simple" }],
      "@typescript-eslint/no-non-null-assertion": "error",
      "@typescript-eslint/no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "lodash",
              message:
                'Import method directly `import [METHOD] from "lodash/[METHOD]"` (safest for bundle size).',
              allowTypeImports: true,
            },
          ],
          patterns: [
            {
              group: ["react"],
              importNamePattern:
                "^(React|Function|Ref|Mutable|CSS|Component|Props|Form)|(Event|Handler|Attributes)$",
              message:
                'Use `React.[TYPE]` (e.g. `React.ReactNode`) instead of importing it directly from "react".',
            },
          ],
        },
      ],
      "@typescript-eslint/no-unused-expressions": ["error", { allowTernary: true }],
      "@typescript-eslint/no-unused-vars": ["error", { args: "none", ignoreRestSiblings: true }],
      camelcase: [
        "error",
        {
          properties: "never", // TODO: remove when server responses are camel case
          allow: [
            "MRT_", // For material-react-table
          ],
        },
      ],
      curly: "error",
      "jsdoc/no-defaults": "off",
      "jsdoc/require-jsdoc": "off",
      "jsdoc/require-hyphen-before-param-description": "warn",
      "jsdoc/tag-lines": ["warn", "any", { startLines: 1 }], // Expected 1 line after block description
      "license-header/header": ["error", "license-header.js"],
      "no-console": "warn",
      "no-duplicate-imports": "error",
      "no-param-reassign": [
        "error",
        {
          props: true,
          ignorePropertyModificationsForRegex: [
            // For immer, 'acc' for
            "^draft",
            // For `Array.prototype.reduce()`
            "acc",
            "accumulator",
          ],
        },
      ],
      "no-use-before-define": [
        "error",
        {
          // Function declarations are hoisted, so it’s safe.
          functions: false,
        },
      ],
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
      "react/hook-use-state": "error",
      "react/prop-types": "off",
      "react/self-closing-comp": "error",
      "react-hooks/exhaustive-deps": [
        "warn",
        {
          // Includes hooks from 'react-use'
          additionalHooks:
            "(useSafeMemo|useUpdateEffect|useUpdateEffectOnce|useDeepCompareEffect|useShallowCompareEffect|useCustomCompareEffect)",
        },
      ],
      "require-await": "warn", // TODO: switch to "error" when the quantity of warning will be low
    },
  },
];
