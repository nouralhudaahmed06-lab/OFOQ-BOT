import json
import logging
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# ==========================================================
# أَفُــــق | OFOQ — النسخة الأولى
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
MATERIALS_DIR = BASE_DIR / "materials"
EXAMS_DIR = BASE_DIR / "exams"
CACHE_FILE = BASE_DIR / "file_ids.json"

ENGLISH_URL = "https://alison.com/shop?clear=1&step=chooseCourse"
CHANNEL_URL = "https://t.me/ofoq_academec"
CONTACT_URL = "https://t.me/i_nouralmanfi"

SUBJECTS = {
    "Electricity & Magnetism": "⚡ Electricity & Magnetism",
    "Differential equations": "📐 Differential Equations",
    "Linear algebra": "📊 Linear Algebra",
    "Mechanic Laboratory": "🔬 Mechanic Laboratory",
    "Medical Instrumentation": "🩺 Medical Instrumentation",
    "Principles of Physiology and Anatomy": "🫀 Physiology & Anatomy",
    "Programming C++": "💻 Programming C++",
    "Thermodynamics": "🌡️ Thermodynamics",
    "Ultrasound waves": "🔊 Ultrasound Waves",
    "Vibrations & Waves": "〰️ Vibrations & Waves",
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("OFOQ")


def load_cache():
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


file_cache = load_cache()


def save_cache():
    CACHE_FILE.write_text(
        json.dumps(file_cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 مواد الدراسة", callback_data="materials")],
        [InlineKeyboardButton("📝 الامتحانات السابقة", callback_data="exams")],
        [InlineKeyboardButton("🇬🇧 لغة أنجليزية طبية", url=ENGLISH_URL)],
        [InlineKeyboardButton("📢 قناة أَفُــــق | 𝐎𝐅𝐎𝐐", url=CHANNEL_URL)],
        [InlineKeyboardButton("💬 أي استفسار", url=CONTACT_URL)],
    ])


def back_keyboard(target="main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data=target)]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "نورتي ياحلوه 🌸💖",
        reply_markup=main_keyboard(),
    )


async def show_materials(query):
    rows = []
    for folder, label in SUBJECTS.items():
        if (MATERIALS_DIR / folder).exists():
            rows.append([InlineKeyboardButton(label, callback_data=f"subject:{folder}")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="main")])
    await query.edit_message_text(
        "📚 مواد الدراسة\n\nاختاري المادة:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_exams(query):
    files = sorted(EXAMS_DIR.iterdir(), key=lambda p: p.name.lower()) if EXAMS_DIR.exists() else []
    rows = []
    for i, path in enumerate(files):
        rows.append([InlineKeyboardButton(f"📝 الامتحان {i + 1}", callback_data=f"exam:{i}")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="main")])
    await query.edit_message_text(
        "📝 الامتحانات السابقة\n\nاختاري الامتحان:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_subject(query, folder):
    subject_dir = MATERIALS_DIR / folder
    if not subject_dir.exists():
        await query.answer("الملف غير موجود حالياً.", show_alert=True)
        return

    files = sorted([p for p in subject_dir.rglob("*") if p.is_file()], key=lambda p: p.name.lower())
    rows = []
    for i, path in enumerate(files):
        name = path.stem.replace("_", " ")
        if len(name) > 38:
            name = name[:35] + "..."
        rows.append([InlineKeyboardButton(f"📄 {name}", callback_data=f"mat:{folder}:{i}")])
    rows.append([InlineKeyboardButton("🔙 المواد الدراسية", callback_data="materials")])

    await query.edit_message_text(
        f"📚 {SUBJECTS.get(folder, folder)}\n\nاختاري الملف:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


def get_subject_file(folder, index):
    subject_dir = MATERIALS_DIR / folder
    files = sorted([p for p in subject_dir.rglob("*") if p.is_file()], key=lambda p: p.name.lower())
    if 0 <= index < len(files):
        return files[index]
    return None


def get_exam_file(index):
    files = sorted([p for p in EXAMS_DIR.iterdir() if p.is_file()], key=lambda p: p.name.lower())
    if 0 <= index < len(files):
        return files[index]
    return None


async def send_document(query, path: Path):
    if not path or not path.exists():
        await query.answer("الملف غير موجود حالياً.", show_alert=True)
        return

    await query.answer("جاري تجهيز الملف... ⏳")
    key = str(path.relative_to(BASE_DIR))

    try:
        # بعد أول رفع، نستخدم file_id الدائم بدل إعادة رفع الملف.
        if key in file_cache:
            await query.message.reply_document(
                document=file_cache[key],
                caption=f"📄 {path.stem}",
            )
            return

        with path.open("rb") as document:
            sent = await query.message.reply_document(
                document=document,
                filename=path.name,
                caption=f"📄 {path.stem}",
            )

        file_cache[key] = sent.document.file_id
        save_cache()

    except TelegramError as exc:
        logger.exception("Telegram error while sending %s", path)
        await query.message.reply_text(
            "❌ ما قدرتش نرسل الملف حالياً. جربي مرة ثانية بعد قليل.\n"
            f"التفاصيل التقنية: {exc}"
        )
    except Exception as exc:
        logger.exception("Unexpected error while sending %s", path)
        await query.message.reply_text("❌ حدث خطأ غير متوقع أثناء إرسال الملف.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""

    if data == "main":
        await query.answer()
        await query.edit_message_text("نورتي ياحلوه 🌸💖", reply_markup=main_keyboard())
        return

    if data == "materials":
        await query.answer()
        await show_materials(query)
        return

    if data == "exams":
        await query.answer()
        await show_exams(query)
        return

    if data.startswith("subject:"):
        await query.answer()
        await show_subject(query, data.split(":", 1)[1])
        return

    if data.startswith("mat:"):
        _, folder, index = data.split(":", 2)
        path = get_subject_file(folder, int(index))
        await send_document(query, path)
        return

    if data.startswith("exam:"):
        path = get_exam_file(int(data.split(":", 1)[1]))
        await send_document(query, path)
        return

    await query.answer("اختيار غير معروف.", show_alert=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception", exc_info=context.error)

def main():
    token = os.getenv("BOT_TOKEN","").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN غير موجود. ضعي Bot Token في متغير البيئة BOT_TOKEN."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    logger.info("🚀 OFOQ يعمل الآن...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()