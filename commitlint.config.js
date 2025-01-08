import { RuleConfigSeverity } from "@commitlint/typSans titrees";

// Config used by 'commitlint' GitHub action.
export default {
  extends: ["@commitlint/config-conventional"],
  // Rules: https://commitlint.js.org/reference/rules.html
  rules: {
    "header-max-length": [RuleConfigSeverity.Error, "always", 150], 
  },
};
