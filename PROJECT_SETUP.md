# Nexa Media Solution — Launch Configuration

## 1) Brand & Basic Info
- **Project Name:** Nexa Media Solution
- **Bot Display Name:** Nexa SMM Panel
- **Bot Username:** `@NexaNo1SMMBot`
- **Support Username:** `@NexaNo1Support`
- **Timezone:** `Asia/Kolkata`
- **Default Language:** Hinglish

## 2) Telegram Assets
- **Updates Channel:** https://t.me/NexaNo1Updates
- **Discussion Group:** `@NexaCommunity`
- **Forced Flow:** Channel → Group → Bot

### Welcome Message
```text
Welcome to Nexa SMM Panel 🚀
Fast, secure, and reliable social media growth services.
✅ Instant Order Processing
✅ Secure Payments (Cashfree)
✅ 24×7 Support
Start here: /start
```

### Pinned Onboarding
1. Join updates channel
2. Join community group
3. Start the bot
4. Add wallet balance
5. Select service & place your order

## 3) Admin & Roles
- **Super Admin IDs:** `6646320334`
- **Admin Username(s):** `@NexaNo1Support`
- **Roles:** `SuperAdmin`, `Admin`, `Support`
- **Admin Panel 2FA:** Enabled

## 4) Payment Gateway (Cashfree)
- **Mode:** Live
- **App ID:** `104929343d4e4107a5ca08529a03929401`
- **Secret Key:** `cfsk_ma_prod_••••••••••••••••`
- **Webhook Secret:** Generate separate secret and store in env
- **Webhook URL:** `https://yourdomain.com/api/cashfree/webhook`
- **Minimum Add Money:** ₹100
- **Auto-credit on Webhook:** Enabled

## 5) Wallet & Finance Rules
- **Currency:** INR only
- **Fee Handling:** User bears transaction fees
- **Failed Order Refund:** Auto-refund to wallet
- **Wallet Expiry:** None
- **Manual Wallet Adjustment:** Allowed for admins

## 6) SMM Provider APIs
1. **JustAnotherPanel**
   - Base URL: `https://justanotherpanel.com/api/v2`
   - API Key: `cb44392c••••••••••••••••`
   - Priority: 1
   - Supports: create order, status, refill, cancel
   - Fallback: Enabled
2. **Peakerr API**
   - Base URL: `https://peakerr.com/api/v2`
   - API Key: `0687c3bd••••••••••••••••`
   - Priority: 2
   - Supports: create order, status, refill, cancel
   - Fallback: Enabled

## 7) Service & Pricing Engine
- **Initial Platforms:** Instagram, YouTube, Telegram
- **Default Markup:** +25%
- **Category Markups:**
  - Instagram Followers: +20%
  - Instagram Likes: +25%
  - YouTube Views: +30%
  - Telegram Members: +20%
- **Min/Max Qty:** Provider based
- **Coupons:** Enabled
- **Referral:** Enabled (5%)
- **VIP Tiers:**
  - Silver: 2%
  - Gold: 5%
  - Platinum: 10%

## 8) Moderation & Compliance
- **Blocked Words:** `spam`, `abuse`, `hack`, `fraud`
- **Abuse Policy:** Warn → Repeat = instant ban
- **Unban Template:**
  - “Hello admin, mera account galti se block ho gaya hai. Kindly review.”
- **KYC:** Not required
- **Geo Restriction:** India only

## 9) User Features
- Place order
- Order history
- Live order tracking
- Ticket support
- FAQ AI replies
- Offer broadcasts
- Referral dashboard
- Daily rewards
- Coupon redemption
- Multi-language switch

## 10) Web Panel Requirements
- Customer web app: Yes
- Admin dashboard: Yes
- Admin pages: orders, users, payments, services, reports, tickets, settings
- Report exports: Excel and PDF
- Dark mode: Enabled

## 11) Infrastructure
- Deploy target: VPS
- Database: PostgreSQL
- Redis: Available
- Domain: `panel.nexamediasolution.in`
- SSL: Cloudflare
- Expected load: 500 users/day, 200 orders/day

## 12) Notifications
Admin Telegram alerts for:
- New order
- Failed payment
- Provider failure
- Abuse reports

Email alerts: No
WhatsApp alerts: No

## 13) Legal Pages
- Terms: `/terms`
- Privacy: `/privacy`
- Refund policy: `/refund-policy`

## 14) Build Preferences
- Code style: Enterprise modular
- Priority: Fast launch + robust architecture
- Deadline: ASAP
- Must-have features:
  - Auto service sync from providers
  - Auto price update
  - Smart provider failover
  - Admin broadcast
  - Anti-fraud payment verification
  - User-level discounts
