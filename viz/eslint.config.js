#!/usr/bin/env node
/**
 * eslint.config.js --- flat ESLint configuration for the viewer
 *  *
 *  * Contains:
 *  *   config export
 */

import react from "eslint-plugin-react";

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
    plugins: { react },
    rules: {
      "react/jsx-uses-vars": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      eqeqeq: "error",
      "no-var": "error",
      "prefer-const": "error",
    },
  },
];
