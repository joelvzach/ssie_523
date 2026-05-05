# 🌍 Deploying to Streamlit Cloud

## Quick Deploy (5 minutes)

### Step 1: Push to GitHub
Your code is already on GitHub at `joelvzach/ssie_523` ✅

### Step 2: Connect to Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **"New app"**
3. Connect your GitHub account (if not already connected)
4. Select:
   - **Repository**: `joelvzach/ssie_523`
   - **Branch**: `main` (or `ideal_sim`)
   - **Main file path**: `simulation/visualization/dashboard.py`

### Step 3: Deploy
Click **"Deploy!"** - that's it! 🚀

Your app will be live at: `https://joelvzach-ssie-523-dashboard-xxxxxx.streamlit.app`

---

## What I've Prepared

### Files Created:
1. ✅ **`requirements.txt`** - Dependencies for Streamlit Cloud
2. ✅ **`.streamlit/config.toml`** - Server configuration
3. ✅ **`setup.sh`** - Pre-deployment script

### Dependencies Included:
- `streamlit>=1.28.0` - Dashboard framework
- `plotly>=5.18.0` - Interactive charts
- `pandas>=2.0.0` - Data processing
- `numpy>=1.24.0` - Numerical calculations

---

## Data Files

Your repo includes **189MB** of data files:
- ✅ ACLED conflict data (~115MB)
- ✅ UN Tourism statistics
- ✅ World Bank GDP data
- ✅ Processed/derived datasets

**Streamlit Cloud Free Tier**: 1GB storage limit  
**Your Usage**: 189MB ✅ (plenty of room)

---

## Local Testing

The same `requirements.txt` works locally:

```bash
# From project root
cd /Users/joelvzach/Code/ssie_523

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run simulation/visualization/dashboard.py
```

Dashboard opens at: `http://localhost:8501`

---

## Troubleshooting

### App won't start on Streamlit Cloud

**Check logs:**
1. Click **"Manage app"** (lower right)
2. Click **"Logs"** tab
3. Look for import errors or data loading issues

**Common fixes:**
- Missing dependency → add to `requirements.txt`
- Data file not found → check file path (use `Path(__file__).parent`)
- Memory limit → reduce agent count in config

### Local dashboard works but Cloud doesn't

**Possible causes:**
1. **File paths** - Use relative paths from repo root
2. **Data loading** - Ensure all CSVs are in repo (not gitignored)
3. **Initialization time** - Cloud has timeout (~60s for free tier)

**Solution:** Check that data files are committed:
```bash
git ls-files data/ | head -20
```

### Performance is slow on Cloud

**Optimization tips:**
- Use `@st.cache_data` for data loading (already implemented)
- Reduce agent count for demo (4,000 → 2,000)
- Limit simulation duration for quick demos

---

## Advanced Settings

### Custom Domain (Pro Feature)
If you upgrade to Streamlit Cloud Pro:
- Add custom domain in app settings
- Configure DNS records

### Environment Variables
For API keys or config:
1. Go to **"Manage app"** → **"Secrets"**
2. Add secrets like:
```toml
API_KEY = "your_secret_key"
```
3. Access in code: `st.secrets["API_KEY"]`

---

## Sharing Your App

### Public Link
Share the URL: `https://joelvzach-ssie-523-dashboard-xxxxxx.streamlit.app`

### Embed in Website
```html
<iframe 
  src="https://joelvzach-ssie-523-dashboard-xxxxxx.streamlit.app" 
  width="100%" 
  height="800px">
</iframe>
```

### QR Code
Generate QR code for easy mobile access:
- Use any QR generator with your app URL
- Print for presentations/posters

---

## Cost

**Streamlit Cloud Free Tier:**
- ✅ Unlimited public apps
- ✅ 1GB storage
- ✅ 1,000 app hours/month
- ⚠️ Apps sleep after 7 days inactivity

**Pro Tier ($25/month):**
- ✅ Private apps
- ✅ No sleep
- ✅ More compute resources

**For academic use:** Free tier is sufficient ✅

---

## Next Steps After Deploy

1. ✅ Test the deployed app
2. ✅ Share link with professor
3. ✅ Add link to CV/portfolio
4. ✅ Monitor usage in Streamlit Cloud dashboard

---

**Deployment Date**: May 5, 2026  
**Status**: Ready to deploy 🚀
