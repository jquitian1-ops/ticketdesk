// 15-skill catalog. IDs '1'..'15'. Shared with frontend.
export const SKILLS_CATALOG: ReadonlyArray<{ skillId: string; skillName: string }> = [
  { skillId: "1", skillName: "Frontend" },
  { skillId: "2", skillName: "Backend" },
  { skillId: "3", skillName: "Mobile" },
  { skillId: "4", skillName: "DevOps" },
  { skillId: "5", skillName: "Cloud" },
  { skillId: "6", skillName: "Data Engineering" },
  { skillId: "7", skillName: "Machine Learning" },
  { skillId: "8", skillName: "Security" },
  { skillId: "9", skillName: "QA" },
  { skillId: "10", skillName: "UX/UI" },
  { skillId: "11", skillName: "Product" },
  { skillId: "12", skillName: "Agile" },
  { skillId: "13", skillName: "Leadership" },
  { skillId: "14", skillName: "Architecture" },
  { skillId: "15", skillName: "AI / GenAI" }
];

export const SKILL_ID_SET = new Set(SKILLS_CATALOG.map((s) => s.skillId));

export function getSkillName(skillId: string): string | undefined {
  return SKILLS_CATALOG.find((s) => s.skillId === skillId)?.skillName;
}
