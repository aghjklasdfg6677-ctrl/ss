import telebot
import smtplib
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telebot import types
from telebot.apihelper import ApiTelegramException
from ratelimit import limits, sleep_and_retry

bot_token = '8808429321:AAEDZZkp4hoSgi7UccQL2o5MnyjAFYzSqg8'
bot = telebot.TeleBot(bot_token)

user_data = dict()
DEV_CHANNEL = "@y_6uu"    # قناة الاشتراك الإجباري

def main_menu():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_add_recipient = types.InlineKeyboardButton('📥 أضف إيميل الشركة', callback_data='add_recipient')
    btn_add_sender = types.InlineKeyboardButton('📤 أضف إيميل الشد', callback_data='add_sender')
    btn_set_subject_message = types.InlineKeyboardButton('📝 تعيين الموضوع والكليشة', callback_data='set_subject_message')
    btn_set_interval = types.InlineKeyboardButton('⏱️ تعيين السليب وعدد الرسائل', callback_data='set_interval_message_count')
    btn_start_sending = types.InlineKeyboardButton('🚀 بدء الإرسال', callback_data='start_sending')
    btn_show_accounts = types.InlineKeyboardButton('📂 إيميلاتي المرسلة', callback_data='show_accounts')
    btn_show_all_info = types.InlineKeyboardButton('📊 عرض معلومات الحملة', callback_data='show_all_info')
    btn_clear_all_info = types.InlineKeyboardButton('🗑️ مسح كل المعلومات', callback_data='clear_all_info')
    btn_delete_email = types.InlineKeyboardButton('❌ حذف إيميل محدد', callback_data='delete_email')
    btn_delete_klishes = types.InlineKeyboardButton('🧹 حذف الكليشات والدعم', callback_data='delete_klishes')

    keyboard.add(btn_start_sending, btn_delete_klishes)
    keyboard.add(btn_add_recipient, btn_add_sender)
    keyboard.add(btn_set_subject_message, btn_set_interval)
    keyboard.add(btn_show_all_info, btn_clear_all_info)
    keyboard.add(btn_delete_email, btn_show_accounts)
    return keyboard

def check_subscription(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(chat_id=DEV_CHANNEL, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        sub_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="اشترك في قناة البوت 🔔", url=f"https://t.me/{DEV_CHANNEL.replace('@', '')}")],
                [types.InlineKeyboardButton(text="تحقق من الاشتراك ✅", callback_data="check_sub")]
            ]
        )
        bot.reply_to(message, f'⚠️ عذراً عزيزي!\n\nيجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه:\n🔗 {DEV_CHANNEL}', reply_markup=sub_keyboard)
        return

    add_user_to_data(str(user_id))
    bot.reply_to(message, '✨ أهلاً بك في بوت شد الإيميلات الاحترافي\n\nاختر من الأزرار بالأسفل للبدء بإعداد حملتك:', reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def verify_subscription(call):
    if not check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✅ تم التحقق من اشتراكك بنجاح!", show_alert=True)
    add_user_to_data(str(call.from_user.id))
    bot.send_message(call.message.chat.id, '✨ أهلاً بك في بوت شد الإيميلات الاحترافي', reply_markup=main_menu())

@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = str(message.from_user.id)
    user_info = user_data.get(user_id)
    if user_info:
        user_info['stop_sending'] = True
        bot.reply_to(message, '🛑 تم إيقاف عملية الإرسال بنجاح!')
    else:
        bot.reply_to(message, '⚠️ لم تقم ببدء عملية الإرسال بعد.')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = str(call.message.chat.id)
    add_user_to_data(user_id)

    if call.data == 'add_recipient':
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="📥 أرسل إيميلات الشركة (المستلمة) مفصولة بمسافات:\n\nمثال:\nemail1@tele.com email2@tele.com"
        )
        bot.register_next_step_handler(call.message, add_recipient, user_id)
        
    elif call.data == 'add_sender':
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="📤 أرسل إيميلات الشد (المرسلة) بصيغة البريد:الباسورد (كل إيميل بسطر):\n\nsender1@gmail.com:pass1\nsender2@gmail.com:pass2"
        )
        bot.register_next_step_handler(call.message, add_sender, user_id)
        
    elif call.data == 'set_subject_message':
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="📝 الرجاء إرسال الموضوع والكليشة بهذه الطريقة بالضبط:\n\nالموضوع : نص الكليشة"
        )
        bot.register_next_step_handler(call.message, set_subject_message, user_id)
        
    elif call.data == 'set_interval_message_count':
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text="⏱️ الرجاء إرسال السليب (الثواني) وعدد الرسائل بهذه الطريقة:\n\nالسليب : عدد الرسائل\nمثال: 5:100"
        )
        bot.register_next_step_handler(call.message, set_interval_message_count, user_id)
        
    elif call.data == 'start_sending':
        bot.answer_callback_query(call.id, "🚀 جاري التحقق وبدء الحملة...")
        start_sending(call.message, user_id)
        
    elif call.data == 'show_accounts':
        show_accounts(call.message, user_id)
        
    elif call.data == 'show_all_info':
        show_all_info(call.message, user_id)
        
    elif call.data == 'clear_all_info':
        clear_all_info(call.message, user_id)
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text='🗑️ تم مسح جميع معلومات الحملة بنجاح!',
            reply_markup=main_menu()
        )
        
    elif call.data == 'delete_email':
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text='❌ أرسل رقم البريد الإلكتروني (الترتيب) الذي ترغب في حذفه:'
        )
        bot.register_next_step_handler(call.message, delete_email, user_id)
        
    elif call.data == 'stop_sending':
        stop_sending_callback(call)
        
    elif call.data == 'add_more_subject_message':
        bot.send_message(user_id, '📝 أرسل الموضوع والكليشة الإضافية بالطريقة التالية:\nالموضوع : نص الكليشة')
        bot.register_next_step_handler(call.message, set_subject_message, user_id)
        
    elif call.data == 'finish_subject_message':
        bot.send_message(user_id, '✅ تم حفظ الكليشات بنجاح!', reply_markup=main_menu())
        
    elif call.data == 'delete_klishes':
        delete_klishes(call.message, user_id)

def add_user_to_data(user_id):
    if user_id not in user_data or not isinstance(user_data[user_id], dict):
        user_data[user_id] = {
            'email_senders': [],
            'email_passwords': [],
            'recipients': [],
            'email_subjects': [],
            'email_messages': [],
            'interval_seconds': 2,
            'message_count': 10,
            'current_subject': '',
            'current_message': ''
        }

def add_recipient(message, user_id):
    recipients = message.text.split()
    if recipients:
        user_data[user_id]['recipients'].clear()  
        user_data[user_id]['recipients'].extend(recipients)
        bot.send_message(message.chat.id, '✅ تمت إضافة إيميلات الشركة بنجاح!', reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, '⚠️ خطأ، يرجى المحاولة مرة أخرى.', reply_markup=main_menu())

def add_sender(message, user_id):
    pairs = message.text.split('\n')  
    success, failure = 0, 0
    for pair in pairs:
        if ':' in pair:
            email, pwd = pair.split(':', 1)
            email, pwd = email.strip(), pwd.strip()
            if email and pwd:
                user_data[user_id]['email_senders'].append(email)
                user_data[user_id]['email_passwords'].append(pwd)
                success += 1
            else:
                failure += 1
        else:
            failure += 1
    
    bot.send_message(message.chat.id, f'📊 نتيجة الإضافة:\n✔️ تم إضافة: {success}\n❌ فشل: {failure}', reply_markup=main_menu())

def set_subject_message(message, user_id):
    try:
        subject, email_message = message.text.split(':', 1)
        user_data[user_id]['current_subject'] = subject.strip()
        user_data[user_id]['current_message'] = email_message.strip()
        
        bot.send_message(message.chat.id, '🎯 تم حفظ الكليشة! الآن أرسل إيميل الدعم (الشركة) المخصص لهذه الكليشة:')
        bot.register_next_step_handler(message, set_recipient_email, user_id)
    except ValueError:
        bot.send_message(message.chat.id, '⚠️ خطأ في الصيغة! استخدم الشكل: الموضوع : الكليشة')

def set_recipient_email(message, user_id):
    if len(user_data[user_id]['email_subjects']) >= 5:
        bot.send_message(message.chat.id, '⚠️ لا يمكن إضافة أكثر من 5 كليشات.', reply_markup=main_menu())
        return
    
    recipient_email = message.text.strip()
    user_data[user_id]['email_subjects'].append(user_data[user_id]['current_subject'])
    user_data[user_id]['email_messages'].append(user_data[user_id]['current_message'])
    user_data[user_id]['recipients'].append(recipient_email)
    
    kbd = types.InlineKeyboardMarkup(row_width=2)
    kbd.add(
        types.InlineKeyboardButton(text="نعم ➕", callback_data='add_more_subject_message'),
        types.InlineKeyboardButton(text="انتهاء ✅", callback_data='finish_subject_message')
    )
    bot.send_message(message.chat.id, '✨ تم تعيين إيميل الدعم بنجاح! هل تريد إضافة كليشة أخرى؟', reply_markup=kbd)

def set_interval_message_count(message, user_id):
    try:
        interval_seconds, message_count = message.text.split(':', 1)
        user_data[user_id]['interval_seconds'] = int(interval_seconds.strip())
        user_data[user_id]['message_count'] = int(message_count.strip())
        bot.send_message(message.chat.id, '⏱️ تم تعيين السليب وعدد الرسائل بنجاح!', reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, '⚠️ خطأ في الصيغة! استخدم الشكل: السليب : عدد الرسائل')

def delete_email(message, user_id):
    try:
        idx = int(message.text.strip()) - 1
        if 0 <= idx < len(user_data[user_id]['email_senders']):
            del user_data[user_id]['email_senders'][idx]
            del user_data[user_id]['email_passwords'][idx]
            bot.send_message(message.chat.id, '🗑️ تم حذف البريد الإلكتروني بنجاح!', reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, '⚠️ الرقم غير موجود بالقائمة.', reply_markup=main_menu())
    except ValueError:
        bot.send_message(message.chat.id, '⚠️ يرجى إرسال رقم صحيح.', reply_markup=main_menu())

@sleep_and_retry
@limits(calls=60, period=60)
def send_limited_message(*args, **kwargs):
    return bot.send_message(*args, **kwargs)

@sleep_and_retry
@limits(calls=60, period=60)
def edit_limited_message_text(*args, **kwargs):
    return bot.edit_message_text(*args, **kwargs)

def send_email(sender_email, sender_password, recipient, subject, message):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    msg.add_header('User-Agent', 'iPhone Mail (14F5089a)')

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def send_emails(user_id, user_info):
    success_count = 0
    error_count = 0
    blocked_senders = set()
    messages_sent = 0

    total_messages = user_info['message_count']
    klishes = list(zip(user_info['email_subjects'], user_info['email_messages'], user_info['recipients']))
    if not klishes:
        send_limited_message(user_id, '⚠️ عذراً، لم تقم بإضافة أي كليشات أو إيميلات دعم!')
        return

    sent_msg = send_limited_message(user_id, "🚀 بدأت عملية إرسال الحملة...\nأرسل /stop للإيقاف في أي وقت.")
    prev_msg_id = sent_msg.message_id

    while messages_sent < total_messages:
        if len(blocked_senders) == len(user_info['email_senders']):
            edit_limited_message_text(chat_id=user_id, message_id=prev_msg_id, text="❌ تم إيقاف الحملة: جميع إيميلات الإرسال أصبحت محظورة.")
            return

        for sender, password in zip(user_info['email_senders'], user_info['email_passwords']):
            if sender in blocked_senders:
                continue

            if user_info.get('stop_sending'):
                del user_info['stop_sending']
                edit_limited_message_text(chat_id=user_id, message_id=prev_msg_id, text=f"🛑 تم إيقاف الإرسال يدوياً.\n✔️ تم إرسال: {success_count}")
                return

            sub_idx = messages_sent % len(klishes)
            subject, message, recipient = klishes[sub_idx]

            if send_email(sender, password, recipient, subject, message):
                success_count += 1
                messages_sent += 1
            else:
                error_count += 1
                blocked_senders.add(sender)

            if messages_sent >= total_messages:
                break

            status_text = f"📊 جاري إرسال الحملة...\n✔️ نجاح: {success_count}\n❌ فاشل: {error_count}\n⏳ المتبقي: {total_messages - messages_sent}"
            try:
                edit_limited_message_text(chat_id=user_id, message_id=prev_msg_id, text=status_text)
            except Exception:
                pass

            time.sleep(user_info['interval_seconds'])

    edit_limited_message_text(chat_id=user_id, message_id=prev_msg_id, text=f"✅ اكتملت الحملة بنجاح!\n\n✔️ إجمالي المرسل: {success_count}\n❌ إجمالي الفشل: {error_count}")

def start_sending(message, user_id):
    user_info = user_data[user_id]
    if not user_info['recipients'] and not user_info['email_subjects']:
        bot.send_message(user_id, '⚠️ يرجى إدخال إيميلات الشركة والكليشات أولاً!', reply_markup=main_menu())
        return
    if not user_info['email_senders']:
        bot.send_message(user_id, '⚠️ يرجى إضافة إيميلات الشد المرسلة أولاً!', reply_markup=main_menu())
        return

    threading.Thread(target=send_emails, args=(user_id, user_info)).start()

def show_accounts(message, user_id):
    user_info = user_data[user_id]
    if not user_info['email_senders']:
        bot.send_message(message.chat.id, '📂 لا توجد إيميلات مرسلة مضافة حالياً.', reply_markup=main_menu())
        return
    text = "📂 قائمة إيميلات الشد المضافة:\n\n"
    for i, s in enumerate(user_info['email_senders'], 1):
        text += f"{i}. {s}\n"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

def show_all_info(message, user_id):
    info = user_data[user_id]
    text = (
        f"📊 معلومات الحملة الحالية:\n\n"
        f"📤 عدد إيميلات الشد: {len(info['email_senders'])}\n"
        f"📥 عدد إيميلات الشركات: {len(info['recipients'])}\n"
        f"📝 عدد الكليشات المحفوظة: {len(info['email_subjects'])}\n"
        f"⏱️ السليب بين الرسائل: {info['interval_seconds']} ثواني\n"
        f"🔢 عدد الرسائل المطلوبة: {info['message_count']}\n"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

def clear_all_info(message, user_id):
    user_data[user_id] = {
        'email_senders': [],
        'email_passwords': [],
        'recipients': [],
        'email_subjects': [],
        'email_messages': [],
        'interval_seconds': 2,
        'message_count': 10,
        'current_subject': '',
        'current_message': ''
    }

def delete_klishes(message, user_id):
    user_data[user_id]['email_subjects'].clear()
    user_data[user_id]['email_messages'].clear()
    user_data[user_id]['recipients'].clear()
    bot.send_message(message.chat.id, '🧹 تم حذف جميع الكليشات وإيميلات الدعم بنجاح!', reply_markup=main_menu())

bot.polling()
