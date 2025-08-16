import { render } from "@testing-library/react";
import { Skeleton } from "../skeleton";

describe("Skeleton", () => {
  it("ローディング時にスケルトンが表示される（デフォルトクラス）", () => {
    const { getByTestId } = render(<Skeleton data-testid="skeleton" />);
    const skeleton = getByTestId("skeleton");
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass("bg-accent");
    expect(skeleton).toHaveClass("animate-pulse");
    expect(skeleton).toHaveClass("rounded-md");
  });

  it("className propsで追加クラスが反映される", () => {
    const { getByTestId } = render(
      <Skeleton data-testid="skeleton" className="h-8 w-8" />
    );
    const skeleton = getByTestId("skeleton");
    expect(skeleton).toHaveClass("h-8");
    expect(skeleton).toHaveClass("w-8");
  });

  it("propsの型安全性：div属性が渡せる", () => {
    const { getByTestId } = render(
      <Skeleton data-testid="skeleton" aria-label="loading" />
    );
    const skeleton = getByTestId("skeleton");
    expect(skeleton).toHaveAttribute("aria-label", "loading");
  });
});
