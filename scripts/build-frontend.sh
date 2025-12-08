#!/bin/bash
set -e

echo "🏗️  Building frontend for production..."

cd frontend

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building with Vite..."
npm run build

echo "✅ Frontend built successfully!"
echo "📁 Output: src/static/dashboard/"

cd ..
echo "🎉 Done! Frontend is ready for deployment."
