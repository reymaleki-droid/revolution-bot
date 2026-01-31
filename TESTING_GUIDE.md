# 🧪 Testing Guide - Certificate System

## Quick Test Steps

### 1. Start the Bot
✅ Bot is already running!

---

### 2. Test Certificate Auto-Generation

**Method 1: Use /start command**
1. Open your Telegram bot
2. Send `/start`
3. You'll get +10 points (daily login bonus)
4. If this ranks you up → Certificate auto-generated!

**Method 2: Manually add points (for testing)**
You can manually trigger a rank-up by testing various activities.

**Current Rank Thresholds:**
```
میهن‌پرست: 0-50 points
سرباز: 50-100 points
سرجوخه: 100-200 points
گروهبان: 200-400 points
ستوان: 400-800 points
سروان: 800-1500 points
سرگرد: 1500-2500 points
سرهنگ: 2500-4000 points
سرتیپ: 4000-6000 points
سرلشکر: 6000-8000 points
سپهبد: 8000-10000 points
مارشال: 10000+ points
```

---

### 3. Test Certificate Commands

**View Your Certificates:**
```
/my_certificates
```
Should show list of all certificates

**Download Certificate:**
```
/get_certificate CERT-XXXXXXXXXXXX
```
(Use actual ID from your certificates list)

**Verify Certificate:**
```
/verify_certificate CERT-XXXXXXXXXXXX
```
Should confirm it's valid

---

### 4. Test Rank Card

```
/my_rank_card
```
Should generate and send a beautiful shareable image

---

### 5. Test Impact Metrics

```
/my_impact
```
Should show your impact (may be empty initially)

---

## 🎯 Quick Ways to Earn Points (For Testing)

### Tweet System:
1. Click "توییت عملیاتی  🐦" button
2. Click the generated Twitter link
3. Points: +25

### Email System:
1. Click "ایمیل‌های فشار 📧" button
2. Go to @IRAN_EMAIL_BOT
3. Complete emails
4. Return and confirm: +500 points

### Conduit System:
1. Click "اشتراک Conduit 🌐" button
2. Choose tier
3. Send screenshot
4. Confirm: +10 to +250 points

### Video System:
1. Click "ویدیوی شهادت جهانی 🎥" button
2. Choose platform
3. Submit link
4. Wait for admin approval: +150 to +750 points

---

## ✅ Expected Behavior

### When You Rank Up:

1. **Automatic Notification:**
   ```
   🎉 تبریک! رتبه شما ارتقا یافت! 🎉
   
   📜 یک گواهینامه دیجیتال برای شما صادر شد!
   ```

2. **Certificate Details:**
   - Certificate ID shown
   - QR code mentioned
   - Verification info provided

3. **Image Sent:**
   - Beautiful HD certificate (1920x1080)
   - Contains all your info
   - Scannable QR code

4. **Stored Forever:**
   - Can retrieve with `/get_certificate`
   - Verify with `/verify_certificate`
   - Listed in `/my_certificates`

---

## 🔍 Check Database Tables

To verify tables were created correctly:

```python
import sqlite3
conn = sqlite3.connect('revolution_bot_secure.db')
cursor = conn.cursor()

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

# Check certificates table
cursor.execute("SELECT * FROM certificates;")
print(cursor.fetchall())

conn.close()
```

Should show:
- `certificates` table
- `impact_metrics` table
- `legacy_archive` table

---

## 📂 Check Generated Files

After first certificate is issued:

1. Check `certificates/` folder:
   - Should contain `CERT-XXXXXXXXXXXX.png` files

2. Check `badges/` folder:
   - Should contain rank card images

3. File sizes:
   - Certificates: ~500KB-1MB (HD quality)
   - Rank cards: ~300KB-500KB

---

## 🐛 Common Issues & Solutions

### Issue: "Certificate not found"
**Solution:** Make sure you ranked up. Try earning more points.

### Issue: "No certificates to display"
**Solution:** You need to rank up at least once. Start is rank 0 (میهن‌پرست).

### Issue: "Image not generating"
**Solution:** 
- Check Pillow and qrcode are installed
- Check folder permissions
- Check logs for errors

### Issue: "QR code not scanning"
**Solution:**
- Use a QR scanner app
- Try different lighting
- Image should be clear and not pixelated

### Issue: "Rank not changing"
**Solution:**
- Check point thresholds
- Verify points are being added
- Check database with `/my_stats`

---

## 📊 Verification Checklist

- [ ] Bot starts without errors
- [ ] Certificate tables created in database
- [ ] `/my_certificates` command works
- [ ] Certificate auto-generated on rank-up
- [ ] Certificate image sent automatically
- [ ] `/get_certificate` command works
- [ ] `/verify_certificate` command works
- [ ] `/my_rank_card` generates image
- [ ] `/my_impact` shows metrics
- [ ] QR codes are scannable
- [ ] Persian text displays correctly
- [ ] Images are HD quality
- [ ] Files saved in correct folders

---

## 🎯 Test Scenarios

### Scenario 1: New User
1. User sends `/start`
2. Gets +10 points
3. Becomes "میهن‌پرست" (rank 0)
4. No certificate yet (need rank 1+)

### Scenario 2: Rank Up to سرباز
1. User earns 50 points total
2. Ranks up to "سرباز"
3. **Certificate auto-generated!**
4. Notification sent
5. Image sent
6. Stored in database

### Scenario 3: View Certificates
1. User sends `/my_certificates`
2. Sees list of certificates
3. Sends `/get_certificate CERT-XXX`
4. Receives certificate image

### Scenario 4: Share Rank
1. User sends `/my_rank_card`
2. Receives beautiful card
3. Shares on Instagram/Twitter
4. Others see their achievements

### Scenario 5: Public Verification
1. User shares certificate ID
2. Friend sends `/verify_certificate CERT-XXX`
3. Bot confirms it's valid
4. Shows rank and points
5. Builds trust

---

## 📈 Success Metrics

After implementation, monitor:

1. **Certificate Generation Rate:**
   - How many certificates issued per day?
   - Which ranks most common?

2. **Command Usage:**
   - How often users check certificates?
   - Rank card generation frequency?

3. **Sharing:**
   - How many rank cards generated?
   - Social media engagement?

4. **Verification:**
   - How many verification requests?
   - Public vs private verifications?

5. **Engagement:**
   - Do users work harder for ranks?
   - Does certification increase activity?

---

## 🚀 Next Steps After Testing

1. **Monitor Logs:**
   - Check for certificate generation errors
   - Verify image quality
   - Monitor database growth

2. **User Feedback:**
   - Ask users about certificate design
   - Check if QR codes scan easily
   - See if sharing works well

3. **Optimize:**
   - Adjust image quality if needed
   - Improve certificate design based on feedback
   - Add more impact metrics

4. **Expand:**
   - Phase 2: Real impact tracking
   - Phase 3: Special missions
   - Phase 4: Post-liberation features

---

## 📞 Admin Testing Commands

For quick testing as admin:

```python
# In Python console:
from secure_database import SecureDatabase
db = SecureDatabase()

# Manually add points to test rank-up:
cert = db.add_points(YOUR_USER_ID, 100, 'test')
if cert:
    print(f"Certificate issued: {cert['certificate_id']}")

# Check user's certificates:
certs = db.get_user_certificates(YOUR_USER_ID)
print(f"Total certificates: {len(certs)}")

# Verify a certificate:
result = db.verify_certificate('CERT-XXXXXXXXXXXX')
print(result)
```

---

**Ready to Test!** 🎉

Your bot is running with the full certificate system. Start testing by:
1. Sending `/start` to your bot
2. Earning some points
3. Watching for certificate notifications
4. Trying all the new commands

Good luck! 🦁☀️
