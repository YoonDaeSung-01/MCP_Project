import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

function runtimeServerPlugin(): Plugin {
  let runtimeServer: http.Server | null = null;

  return {
    name: 'runtime-origin-server',
    configureServer(server) {
      const runtimeDir = path.resolve(__dirname, 'runtime');

      runtimeServer = http.createServer((req, res) => {
        // Cross-Origin 격리 및 Python Worker 네트워크 접근 제한 (B01)
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
        res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
        res.setHeader(
          'Content-Security-Policy',
          "default-src 'none'; script-src 'self' 'unsafe-eval' https://cdn.jsdelivr.net; connect-src https://cdn.jsdelivr.net; worker-src 'self' blob:; style-src 'unsafe-inline';"
        );

        const parsedUrl = new URL(req.url || '/', 'http://127.0.0.1:5174');
        let filePath = path.join(runtimeDir, parsedUrl.pathname === '/' ? 'index.html' : parsedUrl.pathname);

        if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
          filePath = path.join(runtimeDir, 'index.html');
        }

        const ext = path.extname(filePath).toLowerCase();
        let contentType = 'text/plain';
        if (ext === '.html') contentType = 'text/html; charset=utf-8';
        else if (ext === '.js') contentType = 'application/javascript; charset=utf-8';
        else if (ext === '.json') contentType = 'application/json; charset=utf-8';

        res.setHeader('Content-Type', contentType);

        fs.readFile(filePath, (err, data) => {
          if (err) {
            res.writeHead(404);
            res.end('Not Found');
            return;
          }
          res.writeHead(200);
          res.end(data);
        });
      });

      runtimeServer.listen(5174, '127.0.0.1', () => {
        console.log('[Runtime Server] Running on http://127.0.0.1:5174 (Isolated Origin)');
      });

      server.httpServer?.on('close', () => {
        if (runtimeServer) {
          runtimeServer.close();
          runtimeServer = null;
        }
      });
    },
    configurePreviewServer(server) {
      const runtimeDir = path.resolve(__dirname, 'runtime');
      runtimeServer = http.createServer((req, res) => {
        // Cross-Origin 격리 및 Python Worker 네트워크 접근 제한 (B01)
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
        res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
        res.setHeader(
          'Content-Security-Policy',
          "default-src 'none'; script-src 'self' 'unsafe-eval' https://cdn.jsdelivr.net; connect-src https://cdn.jsdelivr.net; worker-src 'self' blob:; style-src 'unsafe-inline';"
        );

        const parsedUrl = new URL(req.url || '/', 'http://127.0.0.1:5174');
        let filePath = path.join(runtimeDir, parsedUrl.pathname === '/' ? 'index.html' : parsedUrl.pathname);

        if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
          filePath = path.join(runtimeDir, 'index.html');
        }

        const ext = path.extname(filePath).toLowerCase();
        let contentType = 'text/plain';
        if (ext === '.html') contentType = 'text/html; charset=utf-8';
        else if (ext === '.js') contentType = 'application/javascript; charset=utf-8';

        res.setHeader('Content-Type', contentType);
        fs.readFile(filePath, (err, data) => {
          if (err) {
            res.writeHead(404);
            res.end('Not Found');
            return;
          }
          res.writeHead(200);
          res.end(data);
        });
      });

      runtimeServer.listen(5174, '127.0.0.1');
      server.httpServer?.on('close', () => {
        if (runtimeServer) {
          runtimeServer.close();
          runtimeServer = null;
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), runtimeServerPlugin()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 5173,
    host: '127.0.0.1',
  },
});
