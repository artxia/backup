module.exports = {
  env: {
    node: true,
    es2021: true,
  },
  extends: [
    'airbnb-base',
    'airbnb-typescript/base',
    'plugin:import/recommended',
    'plugin:import/typescript',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    project: [
      'tsconfig.eslint.json',
    ],
    ecmaVersion: 'latest',
  },
  plugins: [
    '@typescript-eslint',
    'import',
  ],
  rules: {
    'no-continue': 'off',
    'no-restricted-syntax': 'off',
    'import/prefer-default-export': 'off',
    'import/no-extraneous-dependencies': [
      'error', { devDependencies: true },
    ],
    'import/order': [
      'error',
      {
        groups: [
          'builtin',
          'external',
          'internal',
          ['sibling', 'parent'],
          'index',
          'unknown',
        ],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
      },
    ],
  },
  settings: {
    'import/resolver': {
      node: {
        extensions: ['.js', '.ts'],
      },
    },
  },
};
