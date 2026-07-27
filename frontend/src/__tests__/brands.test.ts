import { describe, expect, it } from "vitest";
import { brandStyle, NO_BRAND } from "../brands";

describe("brandStyle", () => {
  it("returns default style for null", () => {
    const s = brandStyle(null);
    expect(s.abbr).toBe("?");
    expect(s.color).toBe("#5A626B");
  });

  it("returns default style for empty string", () => {
    expect(brandStyle("").abbr).toBe("?");
  });

  it("matches Роснефть case-insensitively", () => {
    const s = brandStyle("роснефть");
    expect(s.abbr).toBe("Р");
    expect(s.color).toBe("#FFCC00");
  });

  it("matches Лукойл in mixed case", () => {
    const s = brandStyle("Лукойл АЗС");
    expect(s.abbr).toBe("Л");
    expect(s.color).toBe("#E30613");
  });

  it("matches LUKOIL in latin", () => {
    const s = brandStyle("LUKOIL");
    expect(s.abbr).toBe("Л");
  });

  it("matches Газпром", () => {
    expect(brandStyle("Газпромнефть").abbr).toBe("ГН");
  });

  it("returns default for unknown brand", () => {
    expect(brandStyle("SuperFuel 2000").abbr).toBe("?");
  });

  it("NO_BRAND constant is a non-empty string", () => {
    expect(typeof NO_BRAND).toBe("string");
    expect(NO_BRAND.length).toBeGreaterThan(0);
  });
});
