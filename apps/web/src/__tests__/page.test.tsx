import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import Home from "@/app/page";

test("renders the M2 foundation status", () => {
  render(<Home />);

  expect(
    screen.getByRole("heading", {
      level: 1,
      name: "Business development, built on a reliable foundation.",
    }),
  ).toBeDefined();
  expect(screen.getByText("M2 Data foundation")).toBeDefined();
  expect(screen.getByText("No customer data, external messages, or production AI calls are active.")).toBeDefined();
});
