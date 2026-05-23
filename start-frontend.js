#!/usr/bin/env node

/**
 * Frontend Setup & Cleanup Script
 * This script:
 * 1. Deletes old component files
 * 2. Verifies new files exist
 * 3. Starts the dev server
 */

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const projectRoot = __dirname;
const componentDir = path.join(projectRoot, "frontend", "src", "components");
const frontendDir = path.join(projectRoot, "frontend");

console.log("🚀 Frontend Setup Script\n");
console.log(`Project Root: ${projectRoot}\n`);

// ==========================================
// Step 1: Delete old files
// ==========================================
console.log("📦 Cleaning up old files...");
const filesToDelete = [
  "MockData.js",
  "PredictionView_New.jsx",
  "SentimentView_New.jsx",
];

filesToDelete.forEach((file) => {
  const filePath = path.join(componentDir, file);
  if (fs.existsSync(filePath)) {
    try {
      fs.unlinkSync(filePath);
      console.log(`  ✓ Deleted ${file}`);
    } catch (e) {
      console.log(`  ✗ Error deleting ${file}: ${e.message}`);
    }
  }
});

// ==========================================
// Step 2: Verify new files exist
// ==========================================
console.log("\n📋 Verifying component files...");
const requiredFiles = [
  "App.jsx",
  "MockData.jsx",
  "PredictionView.jsx",
  "SentimentView.jsx",
  "DashboardView.jsx",
  "LoginPage.jsx",
];

let allFilesExist = true;
requiredFiles.forEach((file) => {
  const filePath = path.join(componentDir, file);
  if (fs.existsSync(filePath)) {
    console.log(`  ✓ ${file}`);
  } else {
    console.log(`  ✗ ${file} NOT FOUND`);
    allFilesExist = false;
  }
});

if (!allFilesExist) {
  console.error("\n❌ Some required files are missing. Aborting.");
  process.exit(1);
}

console.log("\n✅ All required files present!");

// ==========================================
// Step 3: Start development server
// ==========================================
console.log("\n▶️  Starting development server...\n");

const npm = spawn("npm", ["run", "dev"], {
  cwd: frontendDir,
  stdio: "inherit",
  shell: true,
});

npm.on("error", (err) => {
  console.error("❌ Failed to start dev server:", err);
  process.exit(1);
});

npm.on("close", (code) => {
  if (code !== 0) {
    console.error(`❌ Dev server exited with code ${code}`);
    process.exit(code);
  }
});
