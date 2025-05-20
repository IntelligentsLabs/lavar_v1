import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import path from "path";

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// Add this debug logging middleware to trace all requests
app.use((req, res, next) => {
  console.log("Incoming request:", {
    method: req.method,
    url: req.url,
    path: req.path,
    query: req.query,
    headers: {
      host: req.headers.host,
      referer: req.headers.referer,
      "user-agent": req.headers["user-agent"],
    },
  });
  next();
});

// Existing middleware and route setups...

(async () => {
  const server = await registerRoutes(app);

  // Add specific handler for auth callback to debug
  app.get("/auth/callback", (req, res, next) => {
    console.log("Auth callback route hit directly!", {
      query: req.query,
      state: req.query.state,
      code: req.query.code,
    });
    next(); // Continue to normal processing
  });

  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";
    console.error(`Error occurred: ${message}`, err);
    res.status(status).json({ message });
  });

  // Setup Vite in development
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  // Fallback route logging
  app.use("*", (req, res) => {
    console.log("Fallback route hit for:", req.originalUrl);
    const indexPath = path.resolve(__dirname, "../client/index.html");
    console.log("Attempting to serve:", indexPath);
    res.sendFile(indexPath, (err) => {
      if (err) {
        console.error("Error serving index.html:", err);
        res.status(500).send("Error serving application");
      } else {
        console.log("Successfully served index.html");
      }
    });
  });

  // Logging server start attempts
  const port = 5000;
  server.listen(
    {
      port,
      host: "0.0.0.0",
      reusePort: true,
    },
    () => {
      log(`Serving on port ${port}`);
    },
  );
})();
