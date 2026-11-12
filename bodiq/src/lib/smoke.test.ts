import { describe, it, expect } from "vitest";
import { z } from "zod";
import Papa from "papaparse";
describe("toolchain smoke", () => {
  it("zod + papaparse work", () => {
    const rows = Papa.parse("name,kcal\nرز,130", { header: true }).data;
    expect(z.array(z.object({ name: z.string(), kcal: z.string() })).parse(rows)).toHaveLength(1);
  });
});
