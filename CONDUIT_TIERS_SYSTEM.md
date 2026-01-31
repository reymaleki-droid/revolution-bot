# 🌐 Conduit Tiered Points System

## Overview
The Conduit internet sharing feature now has a **5-tier reward system** based on the amount of data shared with Iranians inside the country.

## Reward Tiers

| Tier | Data Range | Points | Badge | Level |
|------|------------|--------|-------|-------|
| 🥉 | 1-10 GB | 10 | برنز | Bronze |
| 🥈 | 11-50 GB | 30 | نقره | Silver |
| 🥇 | 51-100 GB | 60 | طلا | Gold |
| 💎 | 101-500 GB | 120 | الماس | Diamond |
| 👑 | 500+ GB | 250 | افسانه‌ای | Legendary |

## How It Works

### User Flow:
1. User clicks "اشتراک اینترنت (Conduit) 🌐" button
2. Bot shows instructions with tier table
3. User installs Psiphon Conduit and shares internet
4. User uploads screenshot of Conduit showing data transferred
5. Bot receives screenshot and asks user to select data amount tier
6. User selects appropriate tier from inline keyboard:
   - 🥉 1-10 GB (10 امتیاز)
   - 🥈 11-50 GB (30 امتیاز)
   - 🥇 51-100 GB (60 امتیاز)
   - 💎 101-500 GB (120 امتیاز)
   - 👑 500+ GB (250 امتیاز)
7. Bot awards points based on selected tier
8. Bot shows congratulations message with badge, data amount, and points earned

### Database Changes:
- **conduit_verifications table** now includes:
  - `data_shared` (TEXT): The tier selected (e.g., "1-10", "500+")
  - `points_earned` (INTEGER): Points awarded for this verification

### Configuration Changes:
- **config.py**:
  - Added `CONDUIT_TIERS` dictionary with tier definitions
  - Updated `conduit_instructions` to show tier table
  - Added `conduit_data_select` text for tier selection prompt
  - Updated `conduit_verified` success message with variables: `{badge}`, `{data_amount}`, `{points}`
  - Updated help message to show "10-250 امتیاز (بسته به حجم اشتراک)"

### Code Changes:
- **database.py**:
  - Modified `log_conduit_verification()` to accept `data_shared` and `points_earned` parameters
  - Added fields to conduit_verifications table schema

- **bot.py**:
  - Imported `CONDUIT_TIERS` from config
  - Modified `handle_photo()` to show tier selection buttons after screenshot upload
  - Added `conduit_tier_*` callback handler to process tier selection and award points
  - Stores screenshot file_id temporarily in user_data during tier selection

## Benefits

### For Users:
- **Incentivizes long-term engagement**: Users are rewarded more for sharing more data
- **Fair rewards**: Points scale with actual contribution to the cause
- **Gamification**: Different tiers with badges create achievement motivation
- **Transparency**: Users see exactly how much each tier is worth before selecting

### For the Movement:
- **Encourages sustained Conduit usage**: Higher rewards for 500+ GB motivates users to keep Conduit running
- **Tracks real impact**: Database stores how much data each user shares
- **Flexibility**: Can adjust tier thresholds and rewards based on campaign needs
- **Analytics**: Can track distribution of tier selections to understand contribution patterns

## Example User Experience

```
📱 User clicks Conduit button

🤖 Bot: "🌐 عملیات Conduit - اشتراک اینترنت..."
       Shows installation instructions
       Shows reward tier table:
       🥉 1-10 GB → 10 points
       🥈 11-50 GB → 30 points
       ...

📸 User uploads screenshot

🤖 Bot: "📊 چه مقدار اینترنت را به اشتراک گذاشته‌اید؟"
       Shows 5 inline buttons for tier selection

👆 User selects "💎 101-500 GB (120 امتیاز)"

🤖 Bot: "🎉 تبریک! Conduit شما تأیید شد!
        💎 الماس
        حجم اشتراک: 101-500 GB
        امتیاز دریافتی: +120 ⭐
        مجموع امتیاز: 670
        درجه جدید: فرمانده
        
        شما یک قهرمان واقعی هستید! 🦁☀️💪"
```

## Technical Implementation

### Tier Selection Flow:
```python
# 1. User uploads screenshot
context.user_data['conduit_screenshot_file_id'] = photo.file_id

# 2. Show tier selection keyboard
keyboard = [
    [InlineKeyboardButton("🥉 1-10 GB (10 امتیاز)", callback_data="conduit_tier_1-10")],
    [InlineKeyboardButton("🥈 11-50 GB (30 امتیاز)", callback_data="conduit_tier_11-50")],
    ...
]

# 3. Process tier selection in callback handler
elif data.startswith("conduit_tier_"):
    tier_name = data.replace("conduit_tier_", "")
    tier_info = CONDUIT_TIERS.get(tier_name)
    
    # Award points based on tier
    db.log_conduit_verification(user.id, screenshot_file_id, tier_name, tier_info['points'])
    db.add_points(user.id, tier_info['points'], 'conduit_verified', ...)
```

## Future Enhancements

Possible improvements for the future:
1. **OCR Verification**: Automatically read data amount from screenshot
2. **Historical Tracking**: Show users their cumulative data shared over time
3. **Leaderboard**: Top Conduit sharers by total data
4. **Bonus Multipliers**: Special events with 2x points for Conduit
5. **Milestones**: Special badges for reaching 1TB, 5TB, etc.
6. **Referral System**: Bonus points for recruiting other Conduit users

## Testing

To test the tiered system:
1. Send `/start` to the bot
2. Click "اشتراک اینترنت (Conduit) 🌐"
3. Read the instructions showing the tier table
4. Upload any screenshot as test
5. Select a tier from the buttons
6. Verify points are awarded correctly
7. Check database to confirm data_shared and points_earned are stored

---

*Created: 2026-01-27*
*Status: ✅ Fully Implemented and Working*
