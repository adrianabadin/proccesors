module.exports = {
  env: {
    es2021: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:node/recommended",
    "prettier", // Si usas Prettier
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: "module",
    project: "./tsconfig.json", // opcional si usas type-checking
  },
  plugins: ["@typescript-eslint", "node"],
  rules: {
    // Personaliza tus reglas aquí
    "node/no-unsupported-features/es-syntax": 0,
    "no-console": ["warn"],
    "@typescript-eslint/no-explicit-any": ["warn"],
    "@typescript-eslint/no-unused-vars": ["error"],
  },
  ignorePatterns: ["dist/**/*"],
};
