import * as Sentry from "@sentry/nextjs";
import * as instrumentationClient from "../instrumentation-client";

describe("instrumentation-client.ts", () => {
  it("onRouterTransitionStartがSentry.captureRouterTransitionStartを参照している", () => {
    expect(instrumentationClient.onRouterTransitionStart).toBe(Sentry.captureRouterTransitionStart);
  });
});
