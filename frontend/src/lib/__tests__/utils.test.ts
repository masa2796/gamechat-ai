import { cn } from "../utils";

describe("utils.ts: cn", () => {
  it("clsxとtailwind-mergeでクラス名を正規化する（正常系）", () => {
    expect(cn("a", "b", undefined, false, "c")).toBe("a b c");
    expect(cn("a", "a", "b", "b")).toBe("a a b b"); // tailwind-mergeは既tailwindクラスは重複除去しない
  });

  it("空やfalsy値は除外される", () => {
    expect(cn()).toBe("");
    expect(cn(null, undefined, false, "")).toBe("");
  });

  it("型安全性: ClassValue以外はTypeScriptエラー（実行時はthrowしない）", () => {
    expect(cn(123 as any)).toBe("123");
  });

  it("副作用なし: 入力配列を破壊しない", () => {
    const arr = ["a", "b"];
    cn(...arr);
    expect(arr).toEqual(["a", "b"]);
  });
});
