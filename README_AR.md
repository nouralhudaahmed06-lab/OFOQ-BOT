# أَفُــــق | OFOQ

## تشغيل محلي
1. ثبتي Python.
2. افتحي الطرفية داخل مجلد المشروع.
3. شغلي: `pip install -r requirements.txt`
4. ضعي Bot Token في متغير البيئة `BOT_TOKEN`.
5. شغلي: `python bot.py`

## التشغيل المستمر 24/7
استخدمي خدمة استضافة تدعم Background Worker مثل Render. اربطي المشروع بـ GitHub، واختاري Worker، ثم:
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`
- Environment Variable: `BOT_TOKEN` = Bot Token الخاص بالبوت

لا تضعي الـBot Token داخل الكود أو GitHub.

## ملاحظة
ملف Anatomy & Physiology الكبير تم تقسيمه إلى جزأين أقل من 50 MB لكل جزء حتى يرسله Telegram Bot API.
