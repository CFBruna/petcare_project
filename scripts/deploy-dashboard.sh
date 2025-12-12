#!/bin/bash
set -e

echo "🚀 Deploying TypeScript Dashboard to Production"
echo "================================================"
echo ""

# Step 1: Build Frontend
echo "📦 Step 1/4: Building frontend with Vite..."
cd frontend
npm install --quiet
npm run build
cd ..
echo "✅ Frontend built successfully to src/static/dashboard/"
echo ""

# Step 2: Collect Static Files
echo "📂 Step 2/4: Collecting static files..."
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
echo "✅ Static files collected"
echo ""

# Step 3: Restart Nginx
echo "🔄 Step 3/4: Restarting Nginx..."
docker compose -f docker-compose.prod.yml restart nginx
echo "✅ Nginx restarted"
echo ""

# Step 4: Health Check
echo "🏥 Step 4/4: Running health check..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://petcare.brunadev.com/dashboard/)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Dashboard is live at https://petcare.brunadev.com/dashboard/"
    echo ""
    echo "🎉 Deployment completed successfully!"
else
    echo "⚠️  Warning: Dashboard returned HTTP $HTTP_CODE"
    echo "   Check logs with: docker compose -f docker-compose.prod.yml logs nginx"
fi

echo ""
echo "📖 Next steps:"
echo "   1. Test dashboard: https://petcare.brunadev.com/dashboard/"
echo "   2. Login with: recrutador@petcare.com / avaliar123"
echo "   3. Verify charts and metrics are loading"
