import '@testing-library/jest-dom';
import React from "react";
import { render, screen } from "@testing-library/react";
import { Input } from "../input";

describe("Input", () => {
  it("renders input with placeholder", () => {
    render(<Input placeholder="Type here" />);
    expect(screen.getByPlaceholderText("Type here")).toBeInTheDocument();
  });

  it("applies className", () => {
    render(<Input className="test-class" />);
    expect(screen.getByRole("textbox")).toHaveClass("test-class");
  });
});