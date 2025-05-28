import '@testing-library/jest-dom';
import React from "react";
import { render, screen } from "@testing-library/react";

function Sample() {
  return <div>Hello, Test!</div>;
}

describe("Sample", () => {
  it("renders text", () => {
    render(<Sample />);
    expect(screen.getByText("Hello, Test!")).toBeInTheDocument();
  });
});