// Config used by 'commitlint' and 'pr-title' GitHub Actions

const RuleConfigSeverity = {
  Disabled: 0,
  Warning: 1,
  Error: 2,
}

module.exports = {
  extends: ["@commitlint/config-conventional"],
  // Rules: https://commitlint.js.org/reference/rules.html
  rules: {
    "header-max-length": [RuleConfigSeverity.Error, "always", 150], 
  },
};
