from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
import re

# 🧠 Configura tu token y tu ID como admin
BOT_TOKEN = '7732124616:AAHVeMt9AYcwfzvIKgMUN22b7QverXmWTmM'
ADMIN_ID = '7712576413'  # Ahora como TEXTO

# 📦 Conecta a la base de datos SQLite
conn = sqlite3.connect('usuarios.db', check_same_thread=False)
c = conn.cursor()

# 🔧 Crea la tabla con chat_id como TEXTO
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id TEXT PRIMARY KEY,
        coins INTEGER DEFAULT 0
    )
''')
conn.commit()

# 👤 Comando /me - Corregido para manejar nuevos usuarios correctamente
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    
    # Verificar si el usuario existe primero
    c.execute('SELECT coins FROM users WHERE chat_id = ?', (user_id,))
    result = c.fetchone()
    
    if not result:
        # Si no existe, crearlo con 0 coins
        c.execute('INSERT INTO users (chat_id, coins) VALUES (?, 0)', (user_id,))
        conn.commit()
        coins = 0
    else:
        coins = result[0]
    
    await update.message.reply_text(f"👤 Tu ID de chat: {user_id}\n💰 Coins: {coins}")

# 📲 Comando /recargacel <numero>
async def recargacel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    args = context.args
    if not args or not re.match(r'^\d{9}$', args[0]):
        await update.message.reply_text("❌ Formato inválido. Usa: /recargacel 991234567")
        return

    numero = args[0]

    # Verificar si el usuario existe
    c.execute('SELECT coins FROM users WHERE chat_id = ?', (user_id,))
    result = c.fetchone()
    
    if not result:
        # Si no existe, crearlo con 0 coins y mostrar error
        c.execute('INSERT INTO users (chat_id, coins) VALUES (?, 0)', (user_id,))
        conn.commit()
        await update.message.reply_text("🚫 No tienes suficientes coins.")
        return
    elif result[0] < 1:
        await update.message.reply_text("🚫 No tienes suficientes coins.")
        return

    c.execute('UPDATE users SET coins = coins - 1 WHERE chat_id = ?', (user_id,))
    conn.commit()

    await update.message.reply_text(f"✅ Recarga enviada para el número {numero}. Se descontó 1 coin.")

    # Notifica al admin
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 Usuario {user_id} solicitó recarga al número: {numero}")

# 👑 Comando solo para admin: /darcoins <chat_id> <cantidad>
async def darcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = str(update.effective_chat.id)
    if sender_id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso para usar este comando.")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ Uso incorrecto. Formato:\n/darcoins <chat_id> <cantidad>")
        return
        
    try:
        coins_to_add = int(args[1])
        if coins_to_add <= 0:
            await update.message.reply_text("❌ La cantidad debe ser un número positivo.")
            return
    except ValueError:
        await update.message.reply_text("❌ La cantidad debe ser un número entero.")
        return
    
    user_id = args[0]
    
    # Verificar si es un ID válido
    if not re.match(r'^[-]?\d+$', user_id):
        await update.message.reply_text("❌ El chat_id debe ser un número entero.")
        return

    c.execute('SELECT * FROM users WHERE chat_id = ?', (user_id,))
    if c.fetchone():
        c.execute('UPDATE users SET coins = coins + ? WHERE chat_id = ?', (coins_to_add, user_id))
    else:
        c.execute('INSERT INTO users (chat_id, coins) VALUES (?, ?)', (user_id, coins_to_add))
    conn.commit()

    await update.message.reply_text(f"✅ Se añadieron {coins_to_add} coins al usuario {user_id}.")

# 👥 Comando para ver todos los usuarios (solo admin)
async def verusuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = str(update.effective_chat.id)
    if sender_id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso para usar este comando.")
        return
    
    c.execute('SELECT chat_id, coins FROM users ORDER BY coins DESC')
    users = c.fetchall()
    
    if not users:
        await update.message.reply_text("📊 No hay usuarios registrados.")
        return
    
    mensaje = "📊 Lista de usuarios:\n"
    for user_id, coins in users:
        mensaje += f"ID: {user_id} - Coins: {coins}\n"
    
    await update.message.reply_text(mensaje)

# 🔌 Inicia el bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("recargacel", recargacel))
    app.add_handler(CommandHandler("darcoins", darcoins))
    app.add_handler(CommandHandler("verusuarios", verusuarios))

    print("🤖 Bot Lucifer - Osiptel corriendo...")
    app.run_polling()