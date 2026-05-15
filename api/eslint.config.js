#!/usr/bin/env node
/**
 * eslint.config.js --- flat ESLint configuration for the BFF
 *  *
 *  * Contains:
 *  *   config export
 */

/**
 * Flat ESLint configuration: recommended rules plus prettier alignment.
 */
export default [
  {
    files: ["src/**/*.js", "test/**/*.js"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-console": "off",
      eqeqeq: "error",
      "no-var": "error",
      "prefer-const": "error",
    },
  },
];
