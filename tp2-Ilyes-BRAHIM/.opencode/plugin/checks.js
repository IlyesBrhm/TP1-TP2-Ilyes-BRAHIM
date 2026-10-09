// Checks post-ecriture : des qu'un agent ecrit un fichier .ts, on relance
// typecheck + lint + tests et on colle la sortie dans le resultat de l'outil,
// pour que l'agent voie le rouge sans qu'on ait a le lui demander.
//
// On appelle directement les scripts npm plutot que scripts/checks.sh : le
// depot doit rester portable (le shell "bash" n'existe pas partout).
// (INFRA-231 : un check rouge ne doit pas interrompre l'agent, il l'avertit,
// c'est a lui de corriger.)
export const ChecksPlugin = async ({ $, directory }) => {
  return {
    "tool.execute.after": async (input, output) => {
      if (input.tool !== "edit" && input.tool !== "write") return;
      const file = input.args?.filePath ?? input.args?.path ?? "";
      if (!file.endsWith(".ts")) return;

      const sections = [];
      for (const script of ["typecheck", "lint", "test"]) {
        const res = await $`npm run --silent ${script}`.cwd(directory).quiet().nothrow();
        const text = (res.stdout.toString() + res.stderr.toString()).trim();
        sections.push(`--- ${script} [${res.exitCode === 0 ? "vert" : "ROUGE"}]\n${text}`);
      }
      output.output =
        (output.output ?? "") + "\n\n--- checks post-ecriture ---\n" + sections.join("\n");
    }
  };
};
