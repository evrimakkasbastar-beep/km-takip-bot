import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Loglama ayarları
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram Bot Token (BotFather'dan aldığınız tokenı buraya yazın)
TOKEN = "BURAYA_TELEGRAM_BOT_TOKENINIZI_YAZIN"

# Conversation Durumları
PLAKA, KM_GIR_BASLANGIC = range(2)

# Basit bir bellek içi veritabanı
user_data_db = {}

# Ana Menü Butonları
def get_main_keyboard():
    keyboard = [
        ['🚗 Araç Ekle / Güncelle', '📊 Km Durumu Listele'],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start Komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Merhaba {user.first_name}! 🚗 Araç Km Takip Botuna hoş geldin.\n"
        "Aşağıdaki menüyü kullanarak aracını ekleyebilir ve kilometre takibi yapabilirsin.",
        reply_markup=get_main_keyboard()
    )

# --- ARAÇ EKLEME AKIŞI ---
async def arac_ekle_basla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Lütfen eklemek veya güncellemek istediğiniz aracın **Plakasını** yazın (Örn: 34ABC123):")
    return PLAKA

async def arac_plaka_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plaka = update.message.text.upper().replace(" ", "")
    context.user_data['gecici_plaka'] = plaka
    await update.message.reply_text(f"**{plaka}** plakalı aracın şu anki mevcut (başlangıç) kilometresini giriniz:")
    return KM_GIR_BASLANGIC

async def arac_km_kaydet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Lütfen sadece sayısal bir kilometre değeri giriniz:")
        return KM_GIR_BASLANGIC
    
    user_id = update.effective_user.id
    plaka = context.user_data['gecici_plaka']
    
    if user_id not in user_data_db:
        user_data_db[user_id] = {}
        
    user_data_db[user_id][plaka] = {
        'ilk_km': km,
        'son_km': km,
        'toplam_yol': 0
    }
    
    await update.message.reply_text(
        f"✅ Araç başarıyla kaydedildi!\n🚗 Plaka: {plaka}\n📟 Mevcut Km: {km}",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

# --- KM DURUMU LİSTELEME ---
async def km_listele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_db or not user_data_db[user_id]:
        await update.message.reply_text("📭 Kayıtlı aracınız bulunmamaktadır.")
        return

    rapor = "📊 **Araç Kilometre Raporunuz:**\n\n"
    for plaka, veri in user_data_db[user_id].items():
        rapor += f"🚗 **Plaka:** {plaka}\n"
        rapor += f"📍 İlk Giriş Km: {veri['ilk_km']}\n"
        rapor += f"📟 Güncel Km: {veri['son_km']}\n"
        rapor += "-------------------------\n"
    
    await update.message.reply_text(rapor, reply_markup=get_main_keyboard())

# İptal işlemi
async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("İşlem iptal edildi.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    arac_ekle_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🚗 Araç Ekle / Güncelle$'), arac_ekle_basla)],
        states={
            PLAKA: [MessageHandler(filters.TEXT & ~filters.COMMAND, arac_plaka_al)],
            KM_GIR_BASLANGIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, arac_km_kaydet)]
        },
        fallbacks=[CommandHandler('cancel', iptal)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(arac_ekle_handler)
    app.add_handler(MessageHandler(filters.Regex('^📊 Km Durumu Listele$'), km_listele))

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == '__main__':
    main()
