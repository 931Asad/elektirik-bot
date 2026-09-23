# ТП/ГТП va liniyalar boti

ТП, ГТП raqami yoki liniya nomi yuborilganda joylashuvi, rasmlari va (liniya bo'lsa)
xaritada chizilgan marshrutini qaytaradigan Telegram bot.

## 1. Botni BotFather'da yaratish

1. Telegram'da **@BotFather** ga yozing.
2. `/newbot` buyrug'ini yuboring, keyin bot nomi va username so'raladi (username `bot` bilan
   tugashi kerak, masalan `elektrtp_bot`).
3. Sizga token beriladi — shu ko'rinishda: `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.
   Bu tokenni hech kimga bermang.

## 2. O'z Telegram ID'ingizni bilib olish

Telegram'da **@userinfobot** ga yozing — u sizga ID raqamingizni beradi (masalan `987654321`).
Shu ID admin bo'ladi.

## 3. Serverda o'rnatish

Kompyuter yoki VPS'da (Python 3.10+ bo'lishi kerak):

```bash
# loyihani serverga yuklang (zip'ni chiqarib, papkaga kiring)
cd tpbot

# virtual muhit (tavsiya etiladi)
python3 -m venv venv
source venv/bin/activate      # Windows'da: venv\Scripts\activate

# kutubxonalarni o'rnatish
pip install -r requirements.txt
```

## 4. Sozlash

`.env.example` faylidan nusxa oling:

```bash
cp .env.example .env
```

`.env` faylini oching va:

- `BOT_TOKEN` — BotFather'dan olgan tokeningiz
- `ADMIN_IDS` — sizning Telegram ID'ingiz (bir nechta admin bo'lsa vergul bilan: `111,222`)

## 5. Ishga tushirish

```bash
python3 bot.py
```

Bot ishga tushdi. To'xtatmasdan doim ishlab turishi uchun (kompyuter/server qayta yoqilganda ham)
`systemd` yoki `screen`/`tmux`/`pm2` kabi vositalardan foydalaning — kerak bo'lsa qanday
qilishni ham tushuntirib beraman.

## 6. Botdan foydalanish

### Admin sifatida (siz)

| Buyruq | Vazifasi |
|---|---|
| `/add` | Yangi ТП yoki ГТП qo'shish (tur → raqam → manzil → joylashuv → rasmlar) |
| `/addline` | Yangi liniya qo'shish (nomi → boshi → oxiri → izoh) |
| `/adduser 123456789 Ism Familiya` | Brigada a'zosiga ruxsat berish |
| `/deluser 123456789` | Ruxsatni olib tashlash |
| `/users` | Ruxsat etilganlar ro'yxati |
| `/stats` | Nechta ТП, liniya, foydalanuvchi borligi |
| `/cancel` | Joriy amalni bekor qilish |

`/add` bosilganda bot ketma-ket so'raydi: turi (ТП/ГТП) → raqami → manzili → joylashuvi
(tugma bilan yoki `41.123, 69.456` deb yozib) → rasmlari (bir nechtasini yuborib, oxirida
tugmani bosasiz).

### Oddiy foydalanuvchi (brigada)

Faqat raqamni yozadi:

- `123` yoki `ТП-123` yoki `тп123` — hammasi bir xil natija beradi
- `Л12` yoki `л-12` — liniyani xaritada chizib beradi

Yangi odamni botga qo'shish uchun: u `/start` bosadi, bot unga o'z ID'sini ko'rsatadi,
o'sha ID'ni sizga aytadi, siz `/adduser` bilan qo'shasiz.

## 7. Nima uchun rasmlar tez ochiladi

Rasmlar serverda emas, Telegram'ning o'zida saqlanadi (`file_id` orqali). Shuning uchun
bot qancha rasm bo'lsa ham joy egallamaydi va sekinlashmaydi.

## 8. Kengaytirish uchun g'oyalar (keyinroq qo'shsa bo'ladi)

- **Yaqin atrofdagilar**: foydalanuvchi joylashuvini yuborsa, yaqin ТП lar ro'yxati chiqishi
- **QR-kod**: har bir ТП eshigiga stiker — skaner qilinsa kartochka darrov ochiladi
- **Ish jurnali**: ТП kartochkasida "Remont qo'shish" — sana, nima qilindi, kim qildi
- **Fider bo'yicha qidiruv**: `Ф-7` yozilsa, o'sha fiderdagi barcha ТП lar

Kerak bo'lsa, shu funksiyalarni ham qo'shib beraman — faqat ayting.

## Fayllar tuzilishi

```
tpbot/
├── bot.py              # ishga tushirish nuqtasi
├── config.py            # .env'dan sozlamalarni o'qish
├── database.py           # SQLite baza va qidiruv mantig'i
├── maputils.py            # liniyani xaritaga chizish
├── keyboards.py            # inline tugmalar
├── handlers/
│   ├── search.py            # ТП/ГТП/liniya qidiruvi
│   └── admin.py              # qo'shish va foydalanuvchi boshqaruvi
├── requirements.txt
└── .env.example
```
