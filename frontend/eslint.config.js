const { FlatCompat } = require("@eslint/eslintrc");
const { dirname } = require("path");
const { fileURLToPath } = require("url");

const _filename = fileURLToPath(__filename);
const _dirname = dirname(_filename);

const compat = new FlatCompat({
  baseDirectory: _dirname,
});

module.exports = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
];
