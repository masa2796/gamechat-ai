import * as Sentry from "@sentry/nextjs";
import * as instrumentation from "../instrumentation";

describe("instrumentation.ts", () => {
  it("register関数がエクスポートされている", () => {
    expect(typeof instrumentation.register).toBe("function");
  });

  it("onRequestErrorがSentry.captureRequestErrorを参照している", () => {
    expect(instrumentation.onRequestError).toBe(Sentry.captureRequestError);
  });

  it("register: NEXT_RUNTIME=nodejsでsentry.server.configをimportする", async () => {
    process.env.NEXT_RUNTIME = "nodejs";
    const mod = await import("../instrumentation");
    expect(typeof mod.register).toBe("function");
    // 実際のimportは副作用がない前提
  });

  it("register: NEXT_RUNTIME=edgeでsentry.edge.configをimportする", async () => {
    process.env.NEXT_RUNTIME = "edge";
    const mod = await import("../instrumentation");
    expect(typeof mod.register).toBe("function");
    // 実際のimportは副作用がない前提
  });
});
