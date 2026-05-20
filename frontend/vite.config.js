import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import fs from "fs";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: "serve-assets",
      configureServer(server) {
        const assetsDir = path.resolve(__dirname, "assets");
        server.middlewares.use((req, res, next) => {
          const match = req.url.match(/^\/assets\/(.+)/);
          if (match) {
            const filePath = path.resolve(assetsDir, match[1]);
            const normalized = path.normalize(filePath);
            if (
              !normalized.startsWith(assetsDir + path.sep) &&
              normalized !== assetsDir
            ) {
              next();
              return;
            }
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              const stat = fs.statSync(filePath);
              const ext = path.extname(filePath);
              const mimeTypes = {
                ".mp4": "video/mp4",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
              };
              const mime = mimeTypes[ext] || "application/octet-stream";
              const range = req.headers.range;
              if (range) {
                const parts = range.replace(/bytes=/, "").split("-");
                const start = parseInt(parts[0], 10);
                const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1;
                const chunkSize = end - start + 1;
                res.writeHead(206, {
                  "Content-Range": `bytes ${start}-${end}/${stat.size}`,
                  "Accept-Ranges": "bytes",
                  "Content-Length": chunkSize,
                  "Content-Type": mime,
                });
                fs.createReadStream(filePath, { start, end }).pipe(res);
              } else {
                res.writeHead(200, {
                  "Content-Type": mime,
                  "Content-Length": stat.size,
                  "Accept-Ranges": "bytes",
                });
                fs.createReadStream(filePath).pipe(res);
              }
              return;
            }
          }
          next();
        });
      },
    },
  ],
  server: {},
  resolve: {
    alias: {
      "@assets": path.resolve(__dirname, "assets"),
    },
  },
});
