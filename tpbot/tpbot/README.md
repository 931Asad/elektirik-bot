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
| `/add` | Yangi ТП yoki ГТП qo'shish (tur → raqam → manzil → joylashuv → rasm/video) |
| `/addline` | Yangi liniya qo'shish (nomi → boshi → oxiri → izoh) |
| `/addmedia` | Mavjud ТП/ГТП ga qo'shimcha rasm yoki video qo'shish |
| `/addlog` | ТП/ГТП uchun "nima qilindi / nima kerak" yozuvi qo'shish (ish jurnali) |
| `/adduser 123456789 Ism Familiya` | Brigada a'zosiga ruxsat berish |
| `/deluser 123456789` | Ruxsatni olib tashlash |
| `/users` | Ruxsat etilganlar ro'yxati |
| `/stats` | Nechta ТП, liniya, foydalanuvchi borligi |
| `/cancel` | Joriy amalni bekor qilish |

`/add` bosilganda bot ketma-ket so'raydi: turi (ТП/ГТП) → raqami → manzili → joylashuvi
(tugma bilan yoki `41.123, 69.456` deb yozib) → rasm yoki video (oddiy va dumaloq video ham
qabul qilinadi, bir nechtasini yuborib, oxirida tugmani bosasiz).

`/addmedia` — allaqachon qo'shilgan ТП/ГТП'ga keyinroq yana rasm/video qo'shish uchun.

`/addlog` — masalan "kabel almashtirildi, yana X kerak" kabi yozuvlarni saqlaydi; bu yozuvlar
o'sha ТП/ГТП qidirilganda kartochkada "So'nggi ishlar" sifatida avtomatik ko'rinadi.

### Oddiy foydalanuvchi (brigada)

Faqat raqamni yozadi:

- `123` yoki `ТП-123` yoki `тп123` — hammasi bir xil natija beradi
- `Л12` yoki `л-12` — liniyani xaritada chizib beradi

Yangi odamni botga qo'shish uchun: u `/start` bosadi, bot unga o'z ID'sini ko'rsatadi,
o'sha ID'ni sizga aytadi, siz `/adduser` bilan qo'shasiz.

## 7. Muhim: Render'da ma'lumotlar bazasi haqida

Render'ning bepul tarifida server fayllari **doimiy saqlanmaydi** — har safar kodni yangilab
qayta joylashtirganingizda (GitHub'ga yangi commit yuborib, qayta deploy qilinganda), SQLite
bazasidagi barcha ТП/ГТП/liniya ma'lumotlari **o'chib ketadi** (bot oddiy ishlab turganda,
uxlab-uyg'onib turganda ma'lumot yo'qolmaydi — faqat kodni yangilaganda yo'qoladi).

Buning yechimi ikkita:
- **Kam-kam kod yangilanadi** deb hisoblasangiz — hozircha shu holida qoldirsa ham bo'ladi,
  faqat har yangilanishdan keyin ma'lumotlarni qayta kiritish kerak bo'ladi.
- **Doimiy saqlash kerak** bo'lsa — Render'da arzon "Persistent Disk" (oyiga taxminan $1)
  ulanadi, shunda ma'lumotlar hech qachon o'chmaydi. Kerak bo'lsa, buni ham sozlab beraman.

## 8. Nima uchun rasmlar tez ochiladi

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
