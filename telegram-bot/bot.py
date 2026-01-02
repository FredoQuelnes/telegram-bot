import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# DATA MEMORY
# =========================
user_nim = {}
user_state = {}
user_reminders = {}

# =========================
# MENU
# =========================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Hitung Nilai", callback_data="hitung")],
        [InlineKeyboardButton("🔤 Nilai Huruf", callback_data="huruf")],
        [InlineKeyboardButton("🏆 Nilai Max & Min", callback_data="maxmin")],
        [InlineKeyboardButton("⏰ Tambah Reminder", callback_data="reminder")],
        [InlineKeyboardButton("📋 List Reminder", callback_data="list")],
        [InlineKeyboardButton("🗑️ Hapus Reminder", callback_data="hapus")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 *Bot Tugas Kuliah*\n\n"
        "Login terlebih dahulu:\n"
        "`login NIM`\n\n"
        "Contoh:\n`login 221011234`",
        parse_mode="Markdown"
    )

# =========================
# LOGIN
# =========================
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await update.message.reply_text("❌ Format salah.\nGunakan: `login NIM`")
        return

    user_id = update.effective_user.id
    user_nim[user_id] = parts[1]

    await update.message.reply_text(
        f"✅ Login berhasil\nNIM: {parts[1]}",
        reply_markup=main_menu()
    )

# =========================
# MENU HANDLER
# =========================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_state[user_id] = query.data

    if query.data == "hitung":
        await query.edit_message_text(
            "📊 Masukkan nilai (pisahkan spasi)\n`80 90 75`",
            parse_mode="Markdown"
        )

    elif query.data == "huruf":
        await query.edit_message_text(
            "🔤 Masukkan satu nilai\n`85`",
            parse_mode="Markdown"
        )

    elif query.data == "maxmin":
        await query.edit_message_text(
            "🏆 Masukkan daftar nilai\n`70 80 90`",
            parse_mode="Markdown"
        )

    elif query.data == "reminder":
        await query.edit_message_text(
            "⏰ Format reminder:\n"
            "`HH:MM pesan`\n\n"
            "Contoh:\n`18:30 Kumpul tugas AI`",
            parse_mode="Markdown"
        )

    elif query.data == "list":
        reminders = user_reminders.get(user_id, [])

        if not reminders:
            await query.edit_message_text("📋 Belum ada reminder.")
        else:
            text = "📋 *Daftar Reminder:*\n\n"
            for i, r in enumerate(reminders, 1):
                text += f"{i}. {r}\n"

            await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "hapus":
        reminders = user_reminders.get(user_id, [])

        if not reminders:
            await query.edit_message_text("📭 Tidak ada reminder untuk dihapus.")
            user_state.pop(user_id, None)
        else:
            await query.edit_message_text(
                "🗑️ Masukkan *nomor reminder* yang ingin dihapus\n\n"
                "Contoh: `1`",
                parse_mode="Markdown"
            )

    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ *Bantuan*\n\n"
            "📊 Hitung rata-rata\n"
            "🔤 Nilai huruf\n"
            "🏆 Max & Min\n"
            "⏰ Tambah reminder\n"
            "📋 List reminder\n"
            "🗑️ Hapus reminder",
            parse_mode="Markdown"
        )

# =========================
# SEND REMINDER
# =========================
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏰ *Reminder!*\n\n{job.data}",
        parse_mode="Markdown"
    )

# =========================
# INPUT PROCESS
# =========================
async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_state:
        await update.message.reply_text("❗ Pilih menu terlebih dahulu.")
        return

    mode = user_state[user_id]
    text = update.message.text.strip()

    # HITUNG
    if mode == "hitung":
        values = list(map(int, text.split()))
        avg = sum(values) / len(values)
        await update.message.reply_text(
            f"📊 Rata-rata: *{avg:.2f}*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # HURUF
    elif mode == "huruf":
        nilai = int(text)
        huruf = (
            "A" if nilai >= 85 else
            "B" if nilai >= 75 else
            "C" if nilai >= 65 else
            "D" if nilai >= 50 else "E"
        )
        await update.message.reply_text(
            f"🔤 Nilai {nilai} → *{huruf}*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # MAX MIN
    elif mode == "maxmin":
        values = list(map(int, text.split()))
        await update.message.reply_text(
            f"🏆 Max: *{max(values)}*\n📉 Min: *{min(values)}*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # REMINDER
    elif mode == "reminder":
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Format salah\n`HH:MM pesan`", parse_mode="Markdown")
            return

        time_part, reminder_text = parts
        reminder_time = datetime.strptime(time_part, "%H:%M").time()

        now = datetime.now()
        target = datetime.combine(now.date(), reminder_time)
        if target < now:
            target += timedelta(days=1)

        delay = (target - now).total_seconds()

        user_reminders.setdefault(user_id, []).append(
            f"{time_part} - {reminder_text}"
        )

        context.job_queue.run_once(
            send_reminder,
            delay,
            chat_id=update.effective_chat.id,
            data=reminder_text
        )

        await update.message.reply_text(
            f"✅ Reminder diset pukul *{time_part}*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

    # HAPUS REMINDER
    elif mode == "hapus":
        if not text.isdigit():
            await update.message.reply_text("❌ Masukkan nomor yang valid")
            return

        idx = int(text) - 1
        reminders = user_reminders.get(user_id, [])

        if idx < 0 or idx >= len(reminders):
            await update.message.reply_text("❌ Nomor tidak ditemukan")
            return

        removed = reminders.pop(idx)
        await update.message.reply_text(
            f"🗑️ Reminder dihapus:\n{removed}",
            reply_markup=main_menu()
        )

    user_state.pop(user_id, None)

# =========================
# MAIN
# =========================
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN belum diset")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^login"), login))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_input))

    print("🤖 Bot aktif...")
    app.run_polling()

if __name__ == "__main__":
    main()


