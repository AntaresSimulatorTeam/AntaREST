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
    "plugin:prettier/recommended",
  ],
  plugins: ["react-refresh"],
  ignorePatterns: ["dist", ".eslintrc.cjs"],
  parser: "@typescript-eslint/parser",
  parserOptions: {
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
        properties: "never", // TODO: remove where server responses are camel case.
        allow: [
          "MRT_", // For material-react-table
        ],
      },
    ],
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
    "react/prop-types": "off",
  },
};
