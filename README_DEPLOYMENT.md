# Image to PDF Converter - Deployment Guide

## 🚀 Deploying to Render.com

### Prerequisites
- GitHub account
- Render.com account (free tier works)

### Deployment Steps

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Render.com**
   - Go to [Render.com](https://render.com) and sign in
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `image-to-pdf-converter`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Instance Type**: Select based on your needs
       - Free tier: Works for light usage
       - Starter ($7/month): Recommended for 100+ images
   - Add environment variable:
     - `SECRET_KEY`: Generate a random string
   - Click "Create Web Service"

3. **Alternative: Use Blueprint (Faster)**
   - Render will auto-detect `render.yaml`
   - Click "New +" → "Blueprint"
   - Select your repository
   - Render will configure everything automatically

### Performance Considerations for 100 Images

#### Memory and Timeout
- **Free Tier**: 512MB RAM, may struggle with 100 large images
- **Starter Tier**: 2GB RAM, handles 100 images comfortably
- **Timeout**: Free tier has request timeouts (could be an issue)

#### Optimization Tips
1. **Use Starter Plan or Higher** for production use with 100+ images
2. **Image Optimization**: The script already resizes images to reduce memory
3. **Request Timeout**: Processing 100 images may take 2-5 minutes
   - Consider implementing a job queue (Redis + Celery) for async processing
   - Or use a progress bar and streaming response

#### Recommended Upgrades for Production
If you need to handle 100 images reliably:

```python
# Install additional packages for async processing
pip install celery redis
```

Add a task queue system:
- Use Celery for background processing
- Use Redis for job tracking
- Add a progress endpoint
- Send email when PDF is ready

### File Structure
```
solution/
├── app.py                    # Flask web application
├── image_to_pdf_core.py      # Core PDF generation logic
├── image_to_pdf.py           # Original CLI script (keep for local use)
├── requirements.txt          # Python dependencies
├── render.yaml              # Render deployment config
├── templates/
│   └── index.html           # Web interface
└── README_DEPLOYMENT.md     # This file
```

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Visit http://localhost:5000
```

### Environment Variables (Render Dashboard)
- `SECRET_KEY`: Your secret key for Flask sessions
- `PORT`: Auto-set by Render (usually 10000)

### Monitoring
- Check logs in Render dashboard
- Monitor memory usage
- Set up health check endpoint: `/health`

### Troubleshooting

**Issue: Request timeout with many images**
- Solution: Upgrade to paid plan or implement async processing

**Issue: Out of memory**
- Solution: Increase instance size or process images in batches

**Issue: Slow upload**
- Solution: Client-side compression or batch uploading

### Cost Estimate
- **Free Tier**: $0 (limited usage, 750 hours/month)
- **Starter**: $7/month (better performance, no sleep)
- **Standard**: $25/month (production-ready, 2GB RAM)

### Security Considerations
1. File validation is already implemented
2. Add rate limiting for production
3. Set up CORS if needed
4. Use HTTPS (auto-provided by Render)

### Next Steps for Production
1. Add user authentication
2. Implement job queue for async processing
3. Add email notification when PDF is ready
4. Add progress tracking
5. Set up monitoring and alerts
6. Add file cleanup cron job
