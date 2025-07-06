import { generateWebAppStructuredData, generateBreadcrumbStructuredData, generateFAQStructuredData } from "../structured-data";

describe("structured-data utils", () => {
  it("generateWebAppStructuredData: 正常系", () => {
    const data = generateWebAppStructuredData();
    expect(data["@type"]).toBe("WebApplication");
    expect(data.name).toBe("GameChat AI");
    expect(data.isAccessibleForFree).toBe(true);
    expect(data.url).toMatch(/^https?:\/\//);
  });

  it("generateBreadcrumbStructuredData: 正常系", () => {
    const items = [
      { name: "Home", item: "https://example.com/" },
      { name: "Page", item: "https://example.com/page" }
    ];
    const data = generateBreadcrumbStructuredData(items);
    expect(data["@type"]).toBe("BreadcrumbList");
    expect(data.itemListElement.length).toBe(2);
    expect(data.itemListElement[0].name).toBe("Home");
    expect(data.itemListElement[1].item).toBe("https://example.com/page");
  });

  it("generateBreadcrumbStructuredData: 境界値（空配列）", () => {
    const data = generateBreadcrumbStructuredData([]);
    expect(data.itemListElement).toEqual([]);
  });

  it("generateFAQStructuredData: 正常系", () => {
    const faqs = [
      { question: "Q1", answer: "A1" },
      { question: "Q2", answer: "A2" }
    ];
    const data = generateFAQStructuredData(faqs);
    expect(data["@type"]).toBe("FAQPage");
    expect(data.mainEntity.length).toBe(2);
    expect(data.mainEntity[0].name).toBe("Q1");
    expect(data.mainEntity[1].acceptedAnswer.text).toBe("A2");
  });

  it("generateFAQStructuredData: 境界値（空配列）", () => {
    const data = generateFAQStructuredData([]);
    expect(data.mainEntity).toEqual([]);
  });

  it("型安全性: 型不正な引数でTypeScriptエラー（実行時はthrowしない）", () => {
    // @ts-expect-error 型不正な引数(undefined)でエラーを期待
    expect(() => generateBreadcrumbStructuredData(undefined)).toThrow();
    // @ts-expect-error 型不正な引数(undefined)でエラーを期待
    expect(() => generateFAQStructuredData(undefined)).toThrow();
  });
});
