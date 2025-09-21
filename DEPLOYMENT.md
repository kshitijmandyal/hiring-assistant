# 🚀 Deployment Guide - TalentScout Hiring Assistant

## ✅ **LIVE DEPLOYMENT**
**🎉 Successfully Deployed!**  
**Live URL**: https://talentscout-hiring-assist.streamlit.app/

---

## Option 1: Streamlit Community Cloud (FREE & Recommended) ✅ USED

### Step-by-Step Deployment:

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app"
   - Repository: `kshitijmandyal/hiring-assistant`
   - Branch: `main`
   - Main file path: `TalentScout_HiringAssistant_Streamlit.py`

3. **Configure Secrets (IMPORTANT)**
   - In app settings, go to "Secrets"
   - Add the following:
   ```toml
   GOOGLE_API_KEY = "your-actual-google-api-key-here"
   GEMINI_API_KEY = "your-actual-gemini-api-key-here"
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for deployment
   - Your app will be live at: `https://your-app-name.streamlit.app`

### Features on Streamlit Cloud:
- ✅ FREE hosting
- ✅ Automatic SSL certificate
- ✅ Custom domain support
- ✅ Automatic redeployment on git push
- ✅ Built-in secrets management

---

## Option 2: Heroku (FREE tier available)

### Prerequisites:
- Heroku account
- Heroku CLI installed

### Files needed (already included):
- `requirements.txt` ✅
- `Procfile` (need to create)

### Steps:
1. Create Procfile:
   ```
   web: streamlit run TalentScout_HiringAssistant_Streamlit.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   heroku config:set GOOGLE_API_KEY="your-api-key"
   git push heroku main
   ```

---

## Option 3: Railway (Modern alternative)

1. Go to https://railway.app
2. Connect GitHub repository
3. Add environment variables
4. Deploy automatically

---

## Option 4: Local Network Hosting

### For demo purposes:
```bash
streamlit run TalentScout_HiringAssistant_Streamlit.py --server.port 8501 --server.address 0.0.0.0
```
- Access via: `http://your-ip:8501`
- Good for local demos or presentations

---

## Recommended: Streamlit Cloud

**Why Streamlit Cloud is best for this project:**
1. **Zero cost** - Completely free
2. **Zero configuration** - Just connect GitHub
3. **Professional URL** - Get a clean .streamlit.app domain
4. **Automatic updates** - Redeploys when you push to GitHub
5. **Built for Streamlit** - Optimized performance
6. **Secrets management** - Secure API key storage

## 🎯 Quick Deploy (2 minutes):
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. New app → Select `kshitijmandyal/hiring-assistant`
4. Add API key in secrets
5. Deploy!

Your live URL will be something like: `https://talentscout-hiring-assist.streamlit.app/` ✅ **DEPLOYED**

Perfect for:
- ✅ Demo videos ✅ **COMPLETED**
- ✅ Portfolio showcase ✅ **READY**
- ✅ Assignment submission ✅ **READY**
- ✅ Sharing with recruiters ✅ **READY**
