// frontend/src/setupProxy.js - Create React App Custom Proxy
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production',
      changeOrigin: true,
      secure: true,
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        console.log(`🔄 Proxying: ${req.method} ${req.url} → ${proxyReq.path}`);
      },
      onProxyRes: (proxyRes, req, res) => {
        console.log(`✅ Proxy response: ${proxyRes.statusCode} for ${req.url}`);
      },
      onError: (err, req, res) => {
        console.error(`❌ Proxy error for ${req.url}:`, err.message);
      }
    })
  );
};
