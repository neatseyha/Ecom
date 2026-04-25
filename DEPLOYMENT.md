# Mini E-Commerce Deployment Guide for Render.com

## Prerequisites

- GitHub account
- Render.com account

## Deployment Steps

### 1. Push to GitHub (if you want)

If you want to use GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

Or use Render's option to deploy from local files.

### 2. Deploy on Render.com

#### Option A: Deploy from GitHub

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `your-shop-name`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

#### Option B: Deploy from Local Directory

1. Install Render CLI: `npm install -g render`
2. Run: `render deploy`

### 3. Configure Environment Variables

In Render Dashboard, go to your service → Environment:

Add these variables:

```
TELEGRAM_BOT_TOKEN=8277635671:AAFk00SgNqkE34WNkst_GwlCprCZw3AQCcg
TELEGRAM_CHAT_ID=@teamsupport_channel
SECRET_KEY=your-random-secret-key-here-change-this
```

**Important**: Generate a strong SECRET_KEY for production:

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Deploy

- Click "Manual Deploy" → "Deploy latest commit"
- Wait for build to complete
- Your site will be live at: `https://your-shop-name.onrender.com`

## Files Created for Render

1. **Procfile** - Tells Render how to run the app
2. **runtime.txt** - Specifies Python version
3. **requirements.txt** - Updated with gunicorn
4. **app.py** - Modified to bind to PORT

## Post-Deployment

### Update Telegram Bot

Make sure your Telegram bot is added as an admin to your channel `@teamsupport_channel`

### Test Your Site

1. Visit your Render URL
2. Browse products
3. Add items to cart
4. Test contact form → should send to Telegram

## Troubleshooting

**Build fails:**

- Check logs in Render dashboard
- Verify requirements.txt has all dependencies

**App doesn't start:**

- Check environment variables are set
- Review application logs

**Session not working:**

- Make sure SECRET_KEY is set in environment variables

**Telegram not working:**

- Verify bot token is correct
- Ensure bot is admin of the channel
- Check bot has been started by sending /start

## Free Tier Limits

- Site sleeps after 15 min of inactivity
- 750 hours/month free
- Site may take 30-50 seconds to wake up

## Custom Domain (Optional)

In Render dashboard:

1. Go to Settings → Custom Domain
2. Add your domain
3. Update DNS records as shown

## Keep Site Active

To prevent sleeping, use a service like UptimeRobot to ping your site every 15 minutes.

## Security Notes

- Never commit `.env` file
- Use strong SECRET_KEY in production
- Keep bot token secure
- Add rate limiting for production use
