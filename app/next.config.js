// ~/Downloads/approval-v2/app/next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development', // service worker only in prod
});

module.exports = withPWA({
  reactStrictMode: true,
});
