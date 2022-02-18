module.exports = {
  testEnvironment: 'miniflare',
  testEnvironmentOptions: {
    script: '',
  },
  preset: 'ts-jest',
  collectCoverage: true,
  testPathIgnorePatterns: [
    'dist',
  ],
};
