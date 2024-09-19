module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended", // TODO: replace with recommended-type-checked
    "plugin:@typescript-eslint/stylistic", // TODO: replace with stylistic-type-checked
    "plugin:react/recommended",
    "plugin:react/jsx-runtime",
    "plugin:react-hooks/recommended",
    "plugin:jsdoc/recommended-typescript",
    "plugin:prettier/recommended", // Must be the last one
  ],
  plugins: [
    "license-header",
    "react-refresh",
  ],
  ignorePatterns: [
    "dist", 
    "license-header.js", 
    ".eslintrc.cjs",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    // `ecmaVersion` is automatically sets by `esXXXX` in `env`
    sourceType: "module",
    project: ["./tsconfig.json", "./tsconfig.node.json"],
    tsconfigRootDir: __dirname,
  },
  settings: {
    react: {
      version: "detect",
    },
  },
  rules: {
    "@typescript-eslint/array-type": ["error", { default: "array-simple" }],
    "@typescript-eslint/no-unused-vars": [
      "error",
      { args: "none", ignoreRestSiblings: true },
    ],
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
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],
    "react/hook-use-state": "error",
    "react/prop-types": "off",
    "react/self-closing-comp": "error",
    "require-await": "warn", // TODO: switch to "error" when the quantity of warning will be low
  },
};
