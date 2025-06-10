from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os
from datetime import datetime
import openpyxl

LOGIN, CANTIERE, COMMITTENTE, OPERA, MC, ALTRO = range(6)

UTENTI_AUTORIZZATI = {
    "1234": "Sauro Salerno",
    "5678": "Angelo Pinto"
}

DATA_FOLDER = "dati"
EXCEL_FILE = os.path.join(DATA_FOLDER, "registro_getti.xlsx")
os.makedirs(DATA_FOLDER, exist_ok=True)

def init_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Data", "Cantiere", "Committente", "Opera", "Quantità_MC", "Firmato_da"])
        wb.save(EXCEL_FILE)

init_excel()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔐 Inserisci il tuo codice di accesso:")
    return LOGIN

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()
    if pin in UTENTI_AUTORIZZATI:
        context.user_data["utente"] = UTENTI_AUTORIZZATI[pin]
        context.user_data["getti"] = []
        context.user_data["data"] = datetime.today().strftime("%d/%m/%Y")
        await update.message.reply_text(f"✅ Benvenuto {UTENTI_AUTORIZZATI[pin]}! Inserisci il nome del cantiere:")
        return CANTIERE
    else:
        await update.message.reply_text("❌ Codice errato. Riprova o digita /annulla per uscire.")
        return LOGIN

async def cantiere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cantiere"] = update.message.text.strip()
    await update.message.reply_text("🏗️ Inserisci il nome del COMMITTENTE:")
    return COMMITTENTE

async def committente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["committente"] = update.message.text.strip()
    await update.message.reply_text("🔧 Inserisci l'opera di riferimento:")
    return OPERA

async def opera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["opera_corrente"] = update.message.text.strip()
    await update.message.reply_text("📏 Inserisci i metri cubi (MC):")
    return MC

async def mc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mc_corrente"] = update.message.text.strip()
    keyboard = [["Si", "No"]]
    await update.message.reply_text("➕ Vuoi aggiungere un altro elemento?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return ALTRO

async def altro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["getti"].append({
        "Opera": context.user_data["opera_corrente"],
        "Quantità_MC": context.user_data["mc_corrente"]
    })
    if update.message.text.strip().lower() == "si":
        await update.message.reply_text("🔧 Inserisci la nuova opera di riferimento:")
        return OPERA

    # salva i dati automaticamente
    utente = context.user_data.get("utente", "N/D")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active

    for g in context.user_data["getti"]:
        ws.append([
            context.user_data["data"],
            context.user_data["cantiere"],
            context.user_data["committente"],
            g["Opera"],
            g["Quantità_MC"],
            utente
        ])
    wb.save(EXCEL_FILE)

    await update.message.reply_text(f"✅ Dati salvati con successo. Firmato automaticamente come: {utente}. Scrivi /start per iniziare un nuovo inserimento.")
    context.user_data.clear()
    return ConversationHandler.END

async def annulla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operazione annullata. Usa /start per ricominciare.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = Application.builder().token("7428970784:AAHzc_8rjKuH4IWUOu_eEcnBCLQyTXY2_Sk").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)],
            CANTIERE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cantiere)],
            COMMITTENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, committente)],
            OPERA: [MessageHandler(filters.TEXT & ~filters.COMMAND, opera)],
            MC: [MessageHandler(filters.TEXT & ~filters.COMMAND, mc)],
            ALTRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, altro)],
        },
        fallbacks=[CommandHandler("annulla", annulla)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("annulla", annulla))
    app.run_polling()
