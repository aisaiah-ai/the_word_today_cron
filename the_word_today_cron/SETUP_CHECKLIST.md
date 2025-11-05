# 📋 Setup Checklist - What You Need Before Running

## ✅ Prerequisites (Required)

### 1. **GCP Project ID** 
   - **Where to find it:**
     ```bash
     gcloud projects list
     ```
   - Or in [GCP Console](https://console.cloud.google.com) → Project Selector (top bar)
   - **Your options:** `aisaiah-sfa-dev-app`, `aisaiahconferencefb`, `oceanic-impact-477020-t8`
   - **Recommended:** `aisaiahconferencefb` (if using Firebase)

### 2. **GitHub Repository** (format: `owner/repo`)
   - **Where to find it:**
     - Check your existing repos: `gh repo list` (if GitHub CLI installed)
     - Or go to [github.com/yourusername](https://github.com) and look at your repositories
     - **Format:** `username/repository-name`
     - **Example:** `johnsmith/python-cron` or `mycompany/the-word-today`
   
   - **If you don't have one:**
     - Repository: `aisaiah-ai/the_word_today_cron`
     - Create at: https://github.com/new (if doesn't exist)
     - Or use: `gh repo create aisaiah-ai/the_word_today_cron --private`

### 3. **YouTube API Key**
   - **Where to get it:**
     1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
     2. Select your project (`aisaiahconferencefb`)
     3. Click **+ CREATE CREDENTIALS** → **API Key**
     4. Copy the key
     5. (Optional) Restrict it to YouTube Data API v3

### 4. **Firebase Service Account Key**
   - **Where to get it:**
     1. Go to [Firebase Console](https://console.firebase.google.com)
     2. Select your project (`aisaiahconferencefb`)
     3. Click ⚙️ **Settings** → **Project settings**
     4. Go to **Service accounts** tab
     5. Click **Generate new private key**
     6. Save the JSON file (e.g., `firebase-key.json`)

## 🔧 Tools Needed (Auto-installed by scripts)

- ✅ `gcloud` CLI - Google Cloud SDK
- ✅ `gh` CLI - GitHub CLI  
- ✅ `jq` - JSON processor

Scripts will try to install these automatically if missing.

## 📝 Quick Reference

| Item | Where to Get It | Example |
|------|----------------|---------|
| **GCP Project ID** | `gcloud projects list` or GCP Console | `aisaiahconferencefb` |
| **GitHub Repo** | github.com/yourusername or create new | `username/repo-name` |
| **YouTube API Key** | Google Cloud Console → APIs & Services → Credentials | `AIzaSy...` |
| **Firebase Key** | Firebase Console → Settings → Service accounts | `firebase-key.json` file |

## 🚀 After Gathering Everything

1. Make sure you're in the `the_word_today_cron` directory
2. Run: `./setup_complete.sh`
3. Enter the values when prompted

## 💡 Pro Tips

- **GCP Project:** Already configured with `gcloud config set project aisaiahconferencefb`
- **GitHub Repo:** If you haven't created one yet, create it at https://github.com/new first
- **API Keys:** Keep them secure - never commit to git!
