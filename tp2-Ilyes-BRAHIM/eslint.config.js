import tseslint from "typescript-eslint";

// Mise en place du lint — ticket INFRA-212.
// Regles recommandées typescript-eslint : le parser seul ne detectait rien.
export default tseslint.config(
  {
    ignores: ["dist/**", "coverage/**", "node_modules/**"]
  },
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.ts", "test/**/*.ts"],
    languageOptions: {
      parserOptions: { ecmaVersion: "latest", sourceType: "module" }
    }
  }
);
