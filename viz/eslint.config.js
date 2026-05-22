#!/usr/bin/env node
/**
 * eslint.config.js --- flat ESLint configuration for the viewer
 *  *
 *  * Contains:
 *  *   config export
 */

/**
 * Flat ESLint configuration for the React viewer sources.
 */
export default [
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      eqeqeq: "error",
      "no-var": "error",
      "prefer-const": "error",
    },
  },
];
