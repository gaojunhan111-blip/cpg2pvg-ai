@echo off
echo Starting CPG2PVG-AI Deployment...
echo.
echo Step 1: Frontend Deployment (Vercel)
echo Opening Vercel deployment page...
start https://vercel.com/new
echo.
echo Instructions:
echo 1. Login with GitHub
echo 2. Select cpg2pvg-ai repository
echo 3. Configure environment variables:
echo    - NEXT_PUBLIC_API_URL: https://your-backend-url.railway.app
echo    - NEXT_PUBLIC_ENVIRONMENT: production
echo    - NEXT_PUBLIC_VERSION: 1.0.0
echo 4. Click Deploy
echo.
pause
echo.
echo Step 2: Backend Deployment (Railway)
echo Opening Railway deployment page...
start https://railway.app/new
echo.
echo Instructions:
echo 1. Login with GitHub
echo 2. Click Deploy from GitHub repo
echo 3. Select cpg2pvg-ai repository
echo 4. Add PostgreSQL database
echo 5. Configure environment variables:
echo    - DATABASE_URL: (get from PostgreSQL service)
echo    - SECRET_KEY: generate secure key
echo    - ENVIRONMENT: production
echo 6. Click Deploy
echo.
pause
echo.
echo Step 3: Database Initialization
echo.
echo Instructions:
echo 1. In Railway console, open PostgreSQL service
echo 2. Click Connect tab
echo 3. Copy DATABASE_URL
echo 4. Connect with PostgreSQL client
echo 5. Run script: scripts/cloud-deployment.sql
echo.
pause
echo.
echo Deployment Complete!
echo Your CPG2PVG-AI system should now be running.
echo.
pause