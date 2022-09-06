module.exports = {
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.(ts|tsx|js|jsx)$": "ts-jest"
  },
  testMatch: ["**/*.test.tsx"],
  setupFilesAfterEnv: [
    "@testing-library/jest-dom/extend-expect"
  ]
};
