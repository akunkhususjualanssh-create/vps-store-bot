#!/usr/bin/env python3
"""VPS Store Bot — GEN SSH STORE
   Inline keyboard untuk semua menu, auto-delete pesan lama saat start"""

import os
import sys
import asyncio
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import BOT_TOKEN, OWNER_ID, OWNER_USERNAME
import database as db

# ─── States ───
OWNER_ADD_PRODUCT = "owner_add_product"
OWNER_BROADCAST = "owner_broadcast"
OWNER_SEND_VPS = "owner_send_vps"
OWNER_SET_QRIS = "owner_set_qris"
OWNER_RESTORE = "owner_restore"
OWNER_EDIT_PRODUCT = "owner_edit_product"
USER_WAITING_PROOF = "waiting_proof"

# ─── Store name ───
STORE_NAME = "GEN SSH STORE"

# ─── Helpers ───
def is_owner(user_id):
    return user_id == OWNER_ID

def main_menu_keyboard():
    kb = [
        [InlineKeyboardButton("📊 PRODUK", callback_data="menu_products"),
         InlineKeyboardButton("🪩 LIST PRODUK", callback_data="menu_list")],
        [InlineKeyboardButton("🛒 PESANAN SAYA", callback_data="menu_orders"),
         InlineKeyboardButton("🛎 HUBUNGI OWNER", callback_data="menu_contact")],
        [InlineKeyboardButton("🔑 MENU OWNER", callback_data="menu_owner")],
    ]
    return InlineKeyboardMarkup(kb)

def owner_menu_keyboard():
    kb = [
        [InlineKeyboardButton(" ADD PRODUK", callback_data="owner_addprod"),
         InlineKeyboardButton(" EDIT PRODUK", callback_data="owner_editprod")],
        [InlineKeyboardButton(" DELETE PRODUK", callback_data="owner_delprod"),
         InlineKeyboardButton(" GANTI QRIS", callback_data="owner_setqris")],
        [InlineKeyboardButton(" KIRIM DATA VPS", callback_data="owner_sendvps"),
         InlineKeyboardButton(" BROADCAST", callback_data="owner_broadcast")],
        [InlineKeyboardButton(" BACKUP DB", callback_data="owner_backup"),
         InlineKeyboardButton(" RESTORE DB", callback_data="owner_restore")],
        [InlineKeyboardButton("⬅️ KEMBALI", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(kb)

def back_to_main_inline():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ KEMBALI", callback_data="back_main")]])

def products_list_keyboard():
    products = db.get_products()
    kb = []
    for p in products:
        kb.append([InlineKeyboardButton(f"📦 {p['name']} — Rp{p['price']:,}", callback_data=f"prod_{p['id']}")])
    kb.append([InlineKeyboardButton("⬅️ KEMBALI", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)

# ─── Main menu text ───
def main_menu_text():
    return (
        f"👑 *{STORE_NAME}*\n\n"
        f"✨ Premium VPS Store\n"
        f"Pilih menu di bawah untuk mulai berbelanja.\n"
        f"Jika butuh bantuan, hubungi owner {OWNER_USERNAME}"
    )

# ─── Start ───
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)

    # Hapus keyboard bawah (ReplyKeyboard) dari versi lama
    try:
        await update.message.reply_text(".", reply_markup=ReplyKeyboardRemove())
        # Hapus pesan "." ini
        await context.bot.delete_message(chat_id=user.id, message_id=update.message.message_id + 1)
    except:
        pass

    # Hapus main menu lama
    old_menu_id = context.user_data.get("menu_msg_id")
    if old_menu_id:
        try:
            await context.bot.delete_message(chat_id=user.id, message_id=old_menu_id)
        except:
            pass

    # Kirim main menu baru
    msg = await update.message.reply_text(
        main_menu_text(),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )
    context.user_data["menu_msg_id"] = msg.message_id

    # Hapus pesan /start dari user
    try:
        await update.message.delete()
    except:
        pass

# ─── Show main menu (edit pesan yang ada) ───
async def show_main_menu(query, context):
    await query.edit_message_text(
        main_menu_text(),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )

# ─── Handle callback ───
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    # ─── Back to main ───
    if data == "back_main":
        await show_main_menu(query, context)
        return

    # ─── Products menu ───
    if data == "menu_products":
        products = db.get_products()
        if not products:
            await query.edit_message_text(
                "📭 Belum ada produk tersedia.\nHubungi admin untuk info produk.",
                reply_markup=back_to_main_inline()
            )
            return
        await query.edit_message_text(
            "📊 *PILIH PRODUK*\n\nKlik produk untuk melihat detail:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=products_list_keyboard()
        )
        return

    # ─── List all products ───
    if data == "menu_list":
        products = db.get_products()
        if not products:
            await query.edit_message_text(
                "📭 Belum ada produk.",
                reply_markup=back_to_main_inline()
            )
            return
        text = "🪩 *LIST PRODUK*\n\n"
        for p in products:
            text += f"• {p['name']} — Rp{p['price']:,}\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_main_inline())
        return

    # ─── Contact ───
    if data == "menu_contact":
        await query.edit_message_text(
            f"🛎 *Hubungi Owner*\n\nSilakan hubungi owner di:\n{OWNER_USERNAME}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    # ─── My orders ───
    if data == "menu_orders":
        orders = db.get_user_orders(user.id)
        if not orders:
            await query.edit_message_text(
                " Kamu belum punya pesanan.",
                reply_markup=back_to_main_inline()
            )
            return
        text = " *PESANAN SAYA*\n\n"
        kb = []
        for o in orders:
            status_emoji = "✅" if o['status'] == 'completed' else "⏳" if o['status'] != 'cancelled' else "❌"
            if o['status'] in ('pending_payment', 'payment_received', 'pending_delivery'):
                status_text = "MASIH DI PROSES\nJika 10-15 menit tidak ada respon, hubungi admin."
            elif o['status'] == 'cancelled':
                status_text = "DIBATALKAN"
            else:
                status_text = "SELESAI"
            text += (
                f"{status_emoji} `{o['order_id']}`\n"
                f" {o['product_name']}\n"
                f" Rp{o['price']:,}\n"
                f" {status_text}\n\n"
            )
            # Tambah tombol batalkan hanya untuk yang masih pending
            if o['status'] in ('pending_payment', 'payment_received', 'pending_delivery'):
                kb.append([InlineKeyboardButton(f"❌ BATALKAN {o['order_id']}", callback_data=f"cancel_{o['order_id']}")])
        kb.append([InlineKeyboardButton("⬅️ KEMBALI", callback_data="back_main")])
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
        return

    # ─── Owner menu ───
    if data == "menu_owner":
        if not is_owner(user.id):
            await query.edit_message_text("❌ Kamu bukan owner!", reply_markup=back_to_main_inline())
            return
        await query.edit_message_text(
            f"🔑 *MENU OWNER*\n\n{STORE_NAME}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )
        return

    # ─── Cancel order ───
    if data.startswith("cancel_"):
        order_id = data.replace("cancel_", "")
        order = db.get_order(order_id)
        if not order or order['user_id'] != user.id:
            await query.edit_message_text("❌ Pesanan tidak ditemukan.", reply_markup=back_to_main_inline())
            return
        kb = [
            [InlineKeyboardButton("✅ YA, BATALKAN", callback_data=f"cancelconf_{order_id}")],
            [InlineKeyboardButton("❌ TIDAK", callback_data="menu_orders")],
        ]
        await query.edit_message_text(
            f"⚠️ *BATALKAN PESANAN?*\n\n"
            f"Order: `{order_id}`\n"
            f"Produk: {order['product_name']}\n"
            f"Total: Rp{order['price']:,}\n\n"
            f"Yakin mau batalkan?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ─── Confirm cancel ───
    if data.startswith("cancelconf_"):
        order_id = data.replace("cancelconf_", "")
        ok = db.cancel_order(order_id)
        if ok:
            await query.edit_message_text(
                f"✅ Pesanan `{order_id}` dibatalkan.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_to_main_inline()
            )
        else:
            await query.edit_message_text(
                "❌ Pesanan tidak bisa dibatalkan (mungkin sudah selesai).",
                reply_markup=back_to_main_inline()
            )
        return

    # ─── View product detail ───
    if data.startswith("prod_"):
        product_id = int(data.replace("prod_", ""))
        product = db.get_product(product_id)
        if not product:
            await query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=back_to_main_inline())
            return
        text = (
            f"📦 *{product['name']}*\n\n"
            f"📝 {product['description'] or '-'}\n\n"
            f"💰 Harga: Rp{product['price']:,}\n"
        )
        kb = [
            [InlineKeyboardButton("🛒 BELI SEKARANG", callback_data=f"buy_{product_id}")],
            [InlineKeyboardButton("⬅️ KEMBALI", callback_data="menu_products")]
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
        return

    # ─── Buy product ───
    if data.startswith("buy_"):
        product_id = int(data.replace("buy_", ""))
        product = db.get_product(product_id)
        if not product:
            await query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=back_to_main_inline())
            return
        order_id = db.create_order(user.id, user.username, user.first_name, product_id, product['name'], product['price'])
        context.user_data['current_order'] = order_id
        context.user_data['state'] = USER_WAITING_PROOF

        qris_file_id = db.get_setting("qris_file_id")

        text = (
            f"🛒 *PESANAN DIBUAT*\n\n"
            f"🆔 Order ID: `{order_id}`\n"
            f"📦 Produk: {product['name']}\n"
            f"💰 Total: Rp{product['price']:,}\n\n"
            f"💳 Silakan transfer ke QRIS di bawah.\n"
            f"Setelah transfer, kirim *screenshot bukti transfer* di sini.\n\n"
            f"⚠️ Pembayaran manual — diverifikasi oleh owner."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_main_inline())

        if qris_file_id:
            await query.message.reply_photo(photo=qris_file_id, caption="💳 QRIS Pembayaran — scan untuk transfer")
        else:
            await query.message.reply_text("⚠️ QRIS belum diset owner. Hubungi admin untuk pembayaran.")
        return

    # ─── Owner actions ───
    if not is_owner(user.id):
        await query.edit_message_text("❌ Kamu bukan owner!", reply_markup=back_to_main_inline())
        return

    if data == "owner_addprod":
        context.user_data["state"] = OWNER_ADD_PRODUCT
        context.user_data["addprod_step"] = "name"
        await query.edit_message_text(
            " *ADD PRODUK*\n\nKirim *nama produk*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    # ─── Edit produk — pilih produk ───
    if data == "owner_editprod":
        products = db.get_products()
        if not products:
            await query.edit_message_text(" Belum ada produk untuk diedit.", reply_markup=back_to_main_inline())
            return
        kb = []
        for p in products:
            kb.append([InlineKeyboardButton(f" {p['name']} — Rp{p['price']:,}", callback_data=f"editprod_{p['id']}")])
        kb.append([InlineKeyboardButton("⬅️ BATAL", callback_data="owner_menu_back")])
        await query.edit_message_text(
            " *EDIT PRODUK*\n\nPilih produk yang mau diedit:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    # ─── Edit produk — pilih field ───
    if data.startswith("editprod_"):
        pid = int(data.replace("editprod_", ""))
        product = db.get_product(pid)
        if not product:
            await query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=back_to_main_inline())
            return
        text = (
            f" *EDIT PRODUK*\n\n"
            f" Nama: {product['name']}\n"
            f" Deskripsi: {product['description'] or '-'}\n"
            f" Harga: Rp{product['price']:,}\n\n"
            f"Pilih field yang mau diedit:"
        )
        kb = [
            [InlineKeyboardButton(" Edit Nama", callback_data=f"edit_name_{pid}")],
            [InlineKeyboardButton(" Edit Deskripsi", callback_data=f"edit_desc_{pid}")],
            [InlineKeyboardButton(" Edit Harga", callback_data=f"edit_price_{pid}")],
            [InlineKeyboardButton("⬅️ KEMBALI", callback_data="owner_editprod")],
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
        return

    # ─── Edit nama ───
    if data.startswith("edit_name_"):
        pid = int(data.replace("edit_name_", ""))
        context.user_data["state"] = OWNER_EDIT_PRODUCT
        context.user_data["edit_prod_id"] = pid
        context.user_data["edit_field"] = "name"
        await query.edit_message_text(
            "✏️ *EDIT NAMA PRODUK*\n\nKirim *nama baru*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    # ─── Edit deskripsi ───
    if data.startswith("edit_desc_"):
        pid = int(data.replace("edit_desc_", ""))
        context.user_data["state"] = OWNER_EDIT_PRODUCT
        context.user_data["edit_prod_id"] = pid
        context.user_data["edit_field"] = "description"
        await query.edit_message_text(
            "✏️ *EDIT DESKRIPSI*\n\nKirim *deskripsi baru*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    # ─── Edit harga ───
    if data.startswith("edit_price_"):
        pid = int(data.replace("edit_price_", ""))
        context.user_data["state"] = OWNER_EDIT_PRODUCT
        context.user_data["edit_prod_id"] = pid
        context.user_data["edit_field"] = "price"
        await query.edit_message_text(
            "✏️ *EDIT HARGA*\n\nKirim *harga baru* (angka saja, contoh: 75000):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    if data == "owner_delprod":
        products = db.get_products()
        if not products:
            await query.edit_message_text("📭 Belum ada produk untuk dihapus.", reply_markup=back_to_main_inline())
            return
        kb = []
        for p in products:
            kb.append([InlineKeyboardButton(f"🗑 {p['name']} (Rp{p['price']:,})", callback_data=f"delprod_{p['id']}")])
        kb.append([InlineKeyboardButton("⬅️ BATAL", callback_data="owner_delprod_cancel")])
        await query.edit_message_text(
            "🗑 *DELETE PRODUK*\n\nPilih produk yang mau dihapus:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if data == "owner_delprod_cancel":
        await query.edit_message_text(
            f"✅ Dibatalkan.\n\n🔑 *MENU OWNER*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )
        return

    if data.startswith("delprod_"):
        pid = int(data.replace("delprod_", ""))
        product = db.get_product(pid)
        if not product:
            await query.edit_message_text("❌ Produk tidak ditemukan.", reply_markup=back_to_main_inline())
            return
        kb = [
            [InlineKeyboardButton("✅ YA, HAPUS", callback_data=f"delconf_{pid}")],
            [InlineKeyboardButton("❌ BATAL", callback_data="owner_delprod")],
        ]
        await query.edit_message_text(
            f"⚠️ *KONFIRMASI HAPUS*\n\n"
            f"Produk: {product['name']}\n"
            f"Harga: Rp{product['price']:,}\n\n"
            f"Yakin mau hapus?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if data.startswith("delconf_"):
        pid = int(data.replace("delconf_", ""))
        product = db.get_product(pid)
        db.delete_product(pid)
        await query.edit_message_text(
            f"✅ Produk *{product['name']}* dihapus!\n\n🔑 *MENU OWNER*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )
        return

    if data == "owner_setqris":
        context.user_data["state"] = OWNER_SET_QRIS
        await query.edit_message_text(
            "🖥 *GANTI QRIS*\n\nKirim *foto QRIS* sekarang:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    if data == "owner_sendvps":
        orders = db.get_pending_orders()
        if not orders:
            await query.edit_message_text(
                "📭 Tidak ada pesanan pending.\n\n🔑 *MENU OWNER*",
                reply_markup=owner_menu_keyboard()
            )
            return
        kb = []
        for o in orders:
            kb.append([InlineKeyboardButton(
                f"📤 {o['order_id']} — {o['product_name']}",
                callback_data=f"sendvps_{o['order_id']}"
            )])
        kb.append([InlineKeyboardButton("⬅️ BATAL", callback_data="owner_menu_back")])
        await query.edit_message_text(
            "💻 *KIRIM DATA VPS*\n\nPilih pesanan:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if data == "owner_menu_back":
        await query.edit_message_text(
            f"✅ Dibatalkan.\n\n🔑 *MENU OWNER*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )
        return

    if data.startswith("sendvps_"):
        order_id = data.replace("sendvps_", "")
        order = db.get_order(order_id)
        if not order:
            await query.edit_message_text("❌ Pesanan tidak ditemukan.", reply_markup=back_to_main_inline())
            return
        context.user_data["state"] = OWNER_SEND_VPS
        context.user_data["vps_order_id"] = order_id
        await query.edit_message_text(
            f"💻 *KIRIM DATA VPS*\n\n"
            f"🆔 Order: `{order_id}`\n"
            f"👤 Buyer: {order['first_name']} (@{order['username'] or '-'})\n"
            f"📦 Produk: {order['product_name']}\n\n"
            f"Silakan masukkan data VPS:\n\n"
            f"```\nIP:\nUser:\nPort:\nPassword:\n```",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    if data == "owner_broadcast":
        context.user_data["state"] = OWNER_BROADCAST
        await query.edit_message_text(
            " *BROADCAST*\n\nKirim pesan untuk semua user:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

    # ─── Backup database ───
    if data == "owner_backup":
        try:
            backup_path = db.backup_database()
            with open(backup_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename="gen_ssh_store_backup.db",
                    caption=" *BACKUP DATABASE*\n\nSimpan file ini untuk restore di bot baru.\nFile berisi: produk, pesanan, users, settings (QRIS).",
                    parse_mode=ParseMode.MARKDOWN
                )
            await query.edit_message_text(
                "✅ Backup berhasil! File dikirim di atas.\n\n *MENU OWNER*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=owner_menu_keyboard()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Backup gagal: {e}",
                reply_markup=owner_menu_keyboard()
            )
        return

    # ─── Restore database ───
    if data == "owner_restore":
        context.user_data["state"] = OWNER_RESTORE
        await query.edit_message_text(
            " *RESTORE DATABASE*\n\nKirim file backup database (.db) yang pernah lu backup.\n\n"
            "⚠️ Data saat ini akan ditimpa dengan data backup!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )
        return

# ─── Handle text (owner conversation states) ───
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()
    state = context.user_data.get("state")

    if state and is_owner(user.id):
        await handle_owner_state(update, context, state, text)
    else:
        # Hapus pesan text dari user, biar chat tetap bersih
        try:
            await update.message.delete()
        except:
            pass

# ─── Handle owner conversation states ───
async def handle_owner_state(update: Update, context: ContextTypes.DEFAULT_TYPE, state, text):
    if state == OWNER_ADD_PRODUCT:
        step = context.user_data.get("addprod_step")
        if step == "name":
            context.user_data["addprod_name"] = text
            context.user_data["addprod_step"] = "desc"
            msg = await update.message.reply_text(
                "✅ Nama tersimpan.\n\nKirim *deskripsi produk*:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_to_main_inline()
            )
        elif step == "desc":
            context.user_data["addprod_desc"] = text
            context.user_data["addprod_step"] = "price"
            msg = await update.message.reply_text(
                "✅ Deskripsi tersimpan.\n\nKirim *harga* (angka saja, contoh: 75000):",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_to_main_inline()
            )
        elif step == "price":
            try:
                price = int(text.replace(".", "").replace(",", "").replace("rp", "").replace("Rp", "").strip())
            except ValueError:
                await update.message.reply_text("❌ Harga harus angka! Contoh: 75000")
                return
            name = context.user_data.pop("addprod_name")
            desc = context.user_data.pop("addprod_desc")
            db.add_product(name, desc, price)
            context.user_data.pop("state", None)
            context.user_data.pop("addprod_step", None)
            await update.message.reply_text(
                f"✅ Produk ditambahkan!\n\n {name}\n Rp{price:,}\n\n *MENU OWNER*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=owner_menu_keyboard()
            )

    elif state == OWNER_EDIT_PRODUCT:
        pid = context.user_data.get("edit_prod_id")
        field = context.user_data.get("edit_field")
        if not pid or not field:
            return

        if field == "price":
            try:
                val = int(text.replace(".", "").replace(",", "").replace("rp", "").replace("Rp", "").strip())
            except ValueError:
                await update.message.reply_text("❌ Harga harus angka!")
                return
            db.update_product(pid, price=val)
        elif field == "name":
            db.update_product(pid, name=text)
        elif field == "description":
            db.update_product(pid, description=text)

        product = db.get_product(pid)
        context.user_data.pop("state", None)
        context.user_data.pop("edit_prod_id", None)
        context.user_data.pop("edit_field", None)

        await update.message.reply_text(
            f"✅ Produk diupdate!\n\n"
            f" Nama: {product['name']}\n"
            f" Deskripsi: {product['description'] or '-'}\n"
            f" Harga: Rp{product['price']:,}\n\n"
            f" *MENU OWNER*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )

    elif state == OWNER_BROADCAST:
        users = db.get_all_users()
        sent = 0
        fail = 0
        progress_msg = await update.message.reply_text(f"📱 Mengirim ke {len(users)} user...")
        for uid in users:
            try:
                await context.bot.send_message(uid, f"📢 {text}")
                sent += 1
                await asyncio.sleep(0.05)
            except:
                fail += 1
        context.user_data.pop("state", None)
        await progress_msg.edit_text(
            f"✅ *Broadcast selesai!*\n\n📤 Terkirim: {sent}\n❌ Gagal: {fail}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )

    elif state == OWNER_SEND_VPS:
        order_id = context.user_data.get("vps_order_id")
        order = db.get_order(order_id)
        if not order:
            await update.message.reply_text("❌ Order tidak ditemukan!", reply_markup=back_to_main_inline())
            context.user_data.pop("state", None)
            return

        vps_text = text
        db.save_vps_data(order_id, vps_text)

        buyer_text = (
            f"✅ *DATA VPS ANDA*\n\n"
            f"🆔 Order: `{order_id}`\n"
            f"📦 Produk: {order['product_name']}\n\n"
            f"{vps_text}\n\n"
            f"Terima kasih sudah berbelanja!\n"
            f"Hubungi {OWNER_USERNAME} jika ada masalah."
        )
        try:
            await context.bot.send_message(order['user_id'], buyer_text, parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        context.user_data.pop("state", None)
        context.user_data.pop("vps_order_id", None)
        await update.message.reply_text(
            f"✅ Data VPS terkirim!\n\n🆔 {order_id}\n👤 {order['first_name']}\n\n🔑 *MENU OWNER*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )

# ─── Handle photo ───
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    file_id = photo.file_id
    state = context.user_data.get("state")

    # Owner restore database via photo? No — restore via document
    if state == OWNER_RESTORE and is_owner(user.id):
        await update.message.reply_text(
            "❌ Kirim file database (.db), bukan foto.",
            reply_markup=back_to_main_inline()
        )
        return

    if state == OWNER_SET_QRIS and is_owner(user.id):
        db.set_setting("qris_file_id", file_id)
        context.user_data.pop("state", None)
        await update.message.reply_text(
            "✅ QRIS disimpan!\n\n🔑 *MENU OWNER*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=owner_menu_keyboard()
        )
        return

    if state == USER_WAITING_PROOF:
        order_id = context.user_data.get("current_order")
        if not order_id:
            await update.message.reply_text("❌ Tidak ada pesanan aktif.", reply_markup=back_to_main_inline())
            return
        order = db.get_order(order_id)
        if not order:
            await update.message.reply_text("❌ Pesanan tidak ditemukan.")
            return

        db.save_payment_proof(order_id, file_id)

        await update.message.reply_text(
            "✅ *BUKTI PEMBAYARAN DITERIMA!*\n\n"
            "Mohon tunggu 10-15 menit.\n"
            "Jika tidak ada respon, hubungi admin.\n\n"
            f"🆔 Order: `{order_id}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_main_inline()
        )

        owner_text = (
            f"🔔 *PESANAN BARU — BUKTI PEMBAYARAN*\n\n"
            f"🆔 Order: `{order_id}`\n"
            f"👤 Buyer: {order['first_name']} (@{order['username'] or '-'})\n"
            f"📦 Produk: {order['product_name']}\n"
            f"💰 Harga: Rp{order['price']:,}\n\n"
            f"Silakan verifikasi & kirim data VPS."
        )
        kb = [
            [InlineKeyboardButton("💻 KIRIM DATA VPS", callback_data=f"sendvps_{order_id}")],
            [InlineKeyboardButton("🔑 MENU OWNER", callback_data="owner_menu_back")]
        ]
        try:
            await context.bot.send_photo(OWNER_ID, photo=file_id, caption=owner_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
        except:
            await context.bot.send_message(OWNER_ID, owner_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))

        context.user_data.pop("state", None)
        context.user_data.pop("current_order", None)
        return

    await update.message.reply_text(" Foto diterima.", reply_markup=back_to_main_inline())

# ─── Handle document (restore database) ───
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    state = context.user_data.get("state")

    if state == OWNER_RESTORE and is_owner(user.id):
        doc = update.message.document
        if not doc:
            return

        # Download file
        file = await doc.get_file()
        backup_path = "/tmp/vps_store_restore.db"
        await file.download_to_drive(backup_path)

        # Restore
        ok = db.restore_database(backup_path)
        context.user_data.pop("state", None)

        if ok:
            await update.message.reply_text(
                "✅ *RESTORE BERHASIL!*\n\n"
                "Database berhasil dipulihkan.\n"
                "Produk, pesanan, users, dan QRIS sudah kembali.\n\n"
                "⚠️ Restart bot agar semua data ter-load dengan benar.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=owner_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Restore gagal! File tidak valid atau bukan database.",
                reply_markup=owner_menu_keyboard()
            )
        return

    await update.message.reply_text(" Dokumen diterima.", reply_markup=back_to_main_inline())

# ─── Main ───
def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info(f"{STORE_NAME} Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
