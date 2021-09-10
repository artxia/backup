const path = require('path');
const WebpackBar = require('webpackbar');
const ESLintPlugin = require('eslint-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

module.exports = {
  mode: process.env.NODE_ENV || 'production',
  target: 'webworker',
  entry: path.join(__dirname, 'src/index.ts'),
  output: {
    filename: 'index.js',
    path: path.join(__dirname, 'dist'),
    library: {
      name: 'rocket-booster',
      type: 'umd',
    },
  },
  resolve: {
    extensions: [
      '.ts',
      '.js',
    ],
  },
  plugins: [
    new WebpackBar({
      color: '#ffafcc',
    }),
    new CleanWebpackPlugin(),
    new ESLintPlugin({
      extensions: ['ts'],
      cache: true,
    }),
  ],
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: 'ts-loader',
      },
    ],
  },
};
