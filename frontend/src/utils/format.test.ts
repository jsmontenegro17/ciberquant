import { describe, expect, it } from "vitest";
import { money, percent } from "./format";
describe("financial display formatters", () => {
  it("formats backend decimal strings without changing their value", () =>
    expect(Number(money("2016.80").replace(/[^0-9]/g, ""))).toBe(201680));
  it("formats percentages consistently", () =>
    expect(percent("54.347826")).toBe("54.35%"));
});
