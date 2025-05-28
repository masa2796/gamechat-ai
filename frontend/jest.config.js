module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.(css|scss)$": "identity-obj-proxy"
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  transform: {
  "^.+\\.(ts|tsx)$": ["ts-jest", { tsconfig: "tsconfig.test.json" }]
  },
  testMatch: [
  "**/__tests__/**/*.{ts,tsx}",
  "**/?(*.)+(spec|test).{ts,tsx}"
  ],
  transformIgnorePatterns: [
    "/node_modules/(?!(lucide-react|@radix-ui|@assistant-ui|remark-gfm|ai)/)",
  ],
};