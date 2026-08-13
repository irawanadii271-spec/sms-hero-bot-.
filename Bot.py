import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
import requests

# ==========================================
# SERVER MINI (Agar Lolos Health Check Render)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot SMS-Hero Running!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

# ==========================================
# KONFIGURASI BOT & API
# ==========================================
BOT_TOKEN = "8364363583:AAEPTVMwnpHDtwwZf-X4kTnBpqxgUBzOMDc"
SMS_HERO_API_KEY = "582c0Aef7648ce44bf433bb9bA200545"

BASE_URL = "https://sms-hero.com/stubs/handler_api.php"

bot = telebot.TeleBot(BOT_TOKEN)

# MENU UTAMA
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    menu_text = (
        "🤖 **Bot SMS-Hero Aktif!**\n\n"
        "Perintah yang bisa digunakan:\n"
        "• `/saldo` - Cek saldo akun\n"
        "• `/beli` - Beli nomor virtual baru\n"
        "• `/otp [ID_ORDER]` - Cek kode OTP\n"
        "• `/selesai [ID_ORDER]` - Selesaikan transaksi\n"
        "• `/batal [ID_ORDER]` - Batalkan transaksi"
    )
    bot.reply_to(message, menu_text, parse_mode="Markdown")

# FITUR 1: CEK SALDO
@bot.message_handler(commands=['saldo'])
def check_balance(message):
    params = {'api_key': SMS_HERO_API_KEY, 'action': 'getBalance'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        res = response.text.strip()
        
        if "ACCESS_BALANCE" in res:
            balance = res.split(":")[1]
            bot.reply_to(message, f"💰 **Saldo Kamu:** ${balance}", parse_mode="Markdown")
        else:
            # Memotong balasan maks 200 karakter agar Telegram tidak meluap/error
            clean_res = res[:200] if len(res) > 200 else res
            bot.reply_to(message, f"❌ Gagal cek saldo:\n`{clean_res}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")


# FITUR 2: BELI NOMOR
@bot.message_handler(commands=['beli'])
def buy_number_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_wa = types.InlineKeyboardButton("💬 WhatsApp", callback_data="buy_wa")
    btn_tg = types.InlineKeyboardButton("✈️ Telegram", callback_data="buy_tg")
    btn_sp = types.InlineKeyboardButton("🛒 Shopee", callback_data="buy_sh")
    btn_go = types.InlineKeyboardButton("🚗 Gojek", callback_data="buy_go")
    markup.add(btn_wa, btn_tg, btn_sp, btn_go)

    bot.send_message(message.chat.id, "📱 **Pilih Layanan:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_buy(call):
    service_code = call.data.split('_')[1]
    params = {
        'api_key': SMS_HERO_API_KEY,
        'action': 'getNumber',
        'service': service_code,
        'country': '0'
    }
    res = requests.get(BASE_URL, params=params).text
    if "ACCESS_NUMBER" in res:
        _, order_id, number = res.split(":")
        msg = (
            f"✅ **Nomor Berhasil Dibeli!**\n\n"
            f"🆔 **ID Order:** `{order_id}`\n"
            f"📞 **Nomor:** `{number}`\n"
            f"🛠 **Layanan:** {service_code.upper()}\n\n"
            f"• Cek OTP: `/otp {order_id}`\n"
            f"• Selesaikan: `/selesai {order_id}`\n"
            f"• Batalkan: `/batal {order_id}`"
        )
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, f"❌ Gagal membeli nomor: {res}")

# FITUR 3: CEK OTP
@bot.message_handler(commands=['otp'])
def check_otp(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ **Format salah!** Gunakan: `/otp [ID_ORDER]`", parse_mode="Markdown")
        return
    
    order_id = args[1]
    params = {'api_key': SMS_HERO_API_KEY, 'action': 'getStatus', 'id': order_id}
    res = requests.get(BASE_URL, params=params).text
    
    if "STATUS_OK" in res:
        code = res.split(":")[1]
        bot.reply_to(message, f"📩 **Kode OTP Kamu:** `{code}`", parse_mode="Markdown")
    elif "STATUS_WAIT_CODE" in res:
        bot.reply_to(message, "⏳ OTP belum masuk, silakan tunggu beberapa saat lalu cek kembali.")
    else:
        bot.reply_to(message, f"ℹ️ Status: {res}")

# FITUR 4: SELESAI / BATAL
@bot.message_handler(commands=['selesai', 'batal'])
def manage_order(message):
    cmd = message.text.split()[0].replace('/', '')
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, f"⚠️ **Format salah!** Gunakan: `/{cmd} [ID_ORDER]`", parse_mode="Markdown")
        return
        
    order_id = args[1]
    status_code = '6' if cmd == 'selesai' else '8'
    params = {'api_key': SMS_HERO_API_KEY, 'action': 'setStatus', 'id': order_id, 'status': status_code}
    res = requests.get(BASE_URL, params=params).text
    bot.reply_to(message, f"ℹ️ Respon server: {res}")

# MENJALANKAN BOT
print("Bot SMS-Hero siap berjalan di Render...")
bot.polling(non_stop=True)
