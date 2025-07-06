import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import type { Mock } from "vitest";

// ErrorBoundaryの簡易モック
class TestErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) {
      return <div data-testid="error-fallback">ErrorBoundary fallback</div>;
    }
    return this.props.children;
  }
}

vi.mock("../useChat", () => ({
  useChat: () => { throw new Error("useChat error!"); }
}));
import AssistantPage from "../index";

describe("AssistantPage ErrorBoundary integration", () => {
  it("useChatがthrowした場合にErrorBoundaryでキャッチされる", () => {
    const { getByTestId } = render(
      <TestErrorBoundary>
        <AssistantPage />
      </TestErrorBoundary>
    );
    expect(getByTestId("error-fallback")).toBeInTheDocument();
  });
});
