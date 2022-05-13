module.exports = {
  testEnvironment: 'miniflare',
  testEnvironmentOptions: {
    script: '',
    kvNamespaces: ["TEST_NAMESPACE"],
  },
  preset: 'ts-jest',
  collectCoverage: true,
  testPathIgnorePatterns: [
    'dist',
  ],
};
