from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
from docx import Document

import os

# TOKEN = os.getenv("TOKEN")
TOKEN="7553779459:AAHz9_Q8Jd7cZBrqrdBHu4qv6Kg2dv3YOcQ"

# Database yaradılması
def create_db():
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS words (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     english_word TEXT UNIQUE NOT NULL, 
                     translation TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def add_word_to_db(word, translation):
    word = word.strip().lower()
    translation = translation.strip()
    
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    c.execute('SELECT * FROM words WHERE LOWER(english_word) = ?', (word,))
    if c.fetchone():
        conn.close()
        return False  # Söz artıq var
    
    c.execute('INSERT INTO words (english_word, translation) VALUES (?, ?)', (word, translation))
    conn.commit()
    conn.close()
    return True  # Söz uğurla əlavə edilib

def show_words():
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    c.execute("SELECT english_word, translation FROM words")
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"📖 {row[0]} - {row[1]}" for row in rows]) if rows else "Hələ heç bir söz əlavə etməmisiniz."

def export_to_word():
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    c.execute("SELECT english_word, translation FROM words")
    rows = c.fetchall()
    conn.close()
    
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Söz'
    hdr_cells[1].text = 'Tərcümə'
    
    for row in rows:
        row_cells = table.add_row().cells
        row_cells[0].text = row[0]
        row_cells[1].text = row[1]
    
    file_name = "words.docx"
    doc.save(file_name)
    return file_name

async def send_file(update: Update, context: CallbackContext):
    file_name = export_to_word()
    with open(file_name, "rb") as f:
        await update.message.reply_document(f)

async def start(update: Update, context: CallbackContext):
    welcome_message = (
        "Salam! 👋 Mən lüğət öyrənmə botuyam!\n\n"
        "✅ Yeni söz əlavə etmək üçün: /new word translation\n"
        "🗑️ Söz silmək üçün: /delete word\n"
        "📖 Bütün sözləri görmək üçün: /show\n"
        "📂 Word faylı əldə etmək üçün: /file"
    )
    await update.message.reply_text(welcome_message)

async def add_word(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    parts = text.split(maxsplit=2)
    
    if len(parts) < 3 or parts[0] != '/new':
        await update.message.reply_text("⚠️ Düzgün format: /new word translation\nMəsələn: /new apple alma")
        return
    
    if add_word_to_db(parts[1], parts[2]):
        await update.message.reply_text(f"✅ {parts[1]} - {parts[2]} uğurla əlavə edildi!")
    else:
        await update.message.reply_text(f"⚠️ {parts[1]} artıq verilənlər bazasında mövcuddur.")

async def delete_word(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    parts = text.split(maxsplit=1)
    
    if len(parts) < 2 or parts[0] != '/delete':
        await update.message.reply_text("⚠️ Düzgün format: /delete word\nMəsələn: /delete apple")
        return
    
    word_to_delete = parts[1].strip().lower()
    conn = sqlite3.connect('words.db')
    c = conn.cursor()
    c.execute('SELECT translation FROM words WHERE LOWER(english_word) = ?', (word_to_delete,))
    row = c.fetchone()
    
    if row:
        c.execute('DELETE FROM words WHERE LOWER(english_word) = ?', (word_to_delete,))
        conn.commit()
        await update.message.reply_text(f"✅ {word_to_delete} - {row[0]} uğurla silindi!")
    else:
        await update.message.reply_text(f"⚠️ {word_to_delete} verilənlər bazasında tapılmadı!")
    
    conn.close()

async def unknown_command(update: Update, context: CallbackContext):
    await update.message.reply_text("⚠️ Yanlış komanda daxil etdiniz! Mövcud komandalar:\n"
                                    "✅ /new word translation\n"
                                    "🗑️ /delete word\n"
                                    "📖 /show\n"
                                    "📂 /file")

async def unknown_message(update: Update, context: CallbackContext):
    await update.message.reply_text("⚠️ Tanınmayan giriş! Zəhmət olmasa düzgün komanda daxil edin.")

def main():
    create_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("show", lambda u, c: u.message.reply_text(show_words())))
    application.add_handler(CommandHandler("file", send_file))
    application.add_handler(MessageHandler(filters.Regex(r'^/new '), add_word))
    application.add_handler(MessageHandler(filters.Regex(r'^/delete '), delete_word))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
    application.run_polling()

if __name__ == '__main__':
    main()
