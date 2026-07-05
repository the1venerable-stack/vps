import os
import asyncio
import logging
import re
import random
import time
from datetime import datetime
from telethon import events
from telethon.sync import TelegramClient

os.system("pip install telethon")

api_id = 23240929
api_hash = 'c86e205a2bca8d6381b30a0d7681bba0'

# ==========================================
# 🛑 إعدادات المالك والجلسات
# ==========================================
OWNER_ID = 123456789  # ⚠️ ضع الايدي (ID) الحقيقي الخاص بك هنا

allowed_sessions = {}  # قاموس لتخزين الجلسات المفعلة { "1234": {"id": 9876543, "name": "أحمد"} }

# فلتر للتحقق مما إذا كان المستخدم هو المالك أو لديه جلسة مفعلة
def is_allowed(event):
    if event.sender_id == OWNER_ID:
        return True
    for session in allowed_sessions.values():
        if session['id'] == event.sender_id:
            return True
    return False

client = TelegramClient(session=None, api_id=api_id, api_hash=api_hash) 
client.start()

publish_active = False

# متغيرات التخزين والرد التلقائي
log_group_id = None
auto_reply_enabled = False
auto_reply_text = ""
auto_reply_cache = {}

# ايموجيات الحماية الفائقة
SUPER_PROTECTION_EMOJIS = ['🃏', '♟', '♦', '♥', '💧', '🌀', '☂', '♣', '❄', '☄', '🔥', '❤‍🔥', '❤️‍🩹', '❤', '💙', '💜', '💚', '✅', '🌹', '💛', '🧡', '🚨', '💞']

def get_sleep_and_text(wait_str, original_text):
    original_text = original_text or ""
    if "-" in str(wait_str):
        try:
            p1, p2 = str(wait_str).split("-")
            sleep_time = random.randint(int(p1.strip()), int(p2.strip()))
        except:
            sleep_time = random.randint(10, 20)
        chosen_emoji = random.choice(SUPER_PROTECTION_EMOJIS)
        new_text = f"{original_text} {chosen_emoji}" if original_text else chosen_emoji
        return sleep_time, new_text
    else:
        try:
            sleep_time = int(wait_str)
        except:
            sleep_time = 10
        return sleep_time, original_text

# ==========================================
# 🛠 أوامر المالك (التنصيب وإدارة الجلسات)
# ==========================================

@client.on(events.NewMessage(pattern=r"^\.تنصيب (.+)$"))
async def setup_session(event):
    if event.sender_id != OWNER_ID:
        return
    await event.delete()
    reply_to = await event.get_reply_message()
    if not reply_to:
        return await event.respond("⚠️ **يجب الرد على رسالة الشخص المراد تفعيله لاستخدام هذا الأمر.**")
    
    user_id = reply_to.sender_id
    name = event.pattern_match.group(1)
    
    # توليد رقم عشوائي فريد للجلسة
    while True:
        session_num = str(random.randint(1000, 9999))
        if session_num not in allowed_sessions:
            break
            
    allowed_sessions[session_num] = {"id": user_id, "name": name}
    await event.respond(f"**✅ تم تنصيب الجلسة بنجاح!**\n👤 **الاسم:** {name}\n🔢 **الرقم:** `{session_num}`\n\nيمكنه الآن استخدام مميزات وأوامر البوت.")

@client.on(events.NewMessage(pattern=r"^\.انهاء (\d+)$"))
async def terminate_session(event):
    if event.sender_id != OWNER_ID:
        return
    await event.delete()
    session_num = event.pattern_match.group(1)
    if session_num in allowed_sessions:
        name = allowed_sessions[session_num]['name']
        del allowed_sessions[session_num]
        await event.respond(f"**✅ تم إنهاء تفعيل الجلسة:** `{name}` (الرقم: {session_num}) بنجاح.")
    else:
        await event.respond("**⚠️ لم يتم العثور على جلسة مفعلة بهذا الرقم.**")

@client.on(events.NewMessage(pattern=r"^\.اظهار الارقام$"))
async def show_sessions(event):
    if event.sender_id != OWNER_ID:
        return
    await event.delete()
    if not allowed_sessions:
        return await event.respond("**لا توجد جلسات مفعلة حالياً.**")
        
    msg = "**📋 قائمة الجلسات المفعلة:**\n\n"
    for num, data in allowed_sessions.items():
        msg += f"👤 **الاسم:** {data['name']} | 🔢 **الرقم:** `{num}`\n"
    await event.respond(msg)

@client.on(events.NewMessage(pattern=r"^\.طريقة التنصيب$"))
async def setup_instructions(event):
    if event.sender_id != OWNER_ID:
        return
    await event.delete()
    text = """**🛠 طريقة استخدام أوامر التنصيب (للمالك فقط):**
    
1️⃣ **لإضافة شخص كـ (جلسة) والسماح له باستخدام البوت:**
قم بالرد على أي رسالة لذلك الشخص واكتب:
`.تنصيب (الاسم)`
*مثال:* `.تنصيب احمد` (وسيقوم البوت بتفعيله وإعطائه رقم عشوائي).

2️⃣ **لإلغاء تفعيل شخص (إنهاء الجلسة):**
اكتب الأمر متبوعاً بالرقم الخاص به:
`.انهاء (الرقم)`
*مثال:* `.انهاء 1234`

3️⃣ **لعرض جميع الأشخاص المفعلين وأرقامهم:**
اكتب الأمر:
`.اظهار الارقام`
"""
    await event.respond(text)


# ==========================================
# 🚀 أوامر البوت الأساسية (للمالك وللجلسات المفعلة)
# ==========================================

async def auto_post_single(client, wait_str, chat, message):
    global publish_active
    publish_active = True
    while publish_active:
        sleep_time, new_text = get_sleep_and_text(wait_str, message.text)
        if message.media:
            await client.send_file(chat, message.media, caption=new_text)
        else:
            await client.send_message(chat, new_text)
        await asyncio.sleep(sleep_time)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.نشر (\S+) (.+)$"))
async def nshr_handler(event):
    await event.delete()
    wait_str = event.pattern_match.group(1)
    chat_usernames = event.pattern_match.group(2).split()
    
    global publish_active
    publish_active = True
    message = await event.get_reply_message()
    if not message:
        return await event.respond("يجب الرد على رسالة لاستخدام هذا الأمر.")

    for chat_username in chat_usernames:
        try:
            chat = await client.get_entity(chat_username)
            await auto_post_single(client, wait_str, chat.id, message)
        except Exception as e:
            await event.respond(f"لا يمكن العثور على المجموعة أو الدردشة {chat_username}: {str(e)}")
        await asyncio.sleep(1)

async def auto_post_groups(client, wait_str, message):
    global publish_active
    publish_active = True
    all_chats = await client.get_dialogs()
    while publish_active:
        for chat in all_chats:
            if not publish_active:
                break
            if chat.is_group:
                sleep_time, new_text = get_sleep_and_text(wait_str, message.text)
                try:
                    if message.media:
                        await client.send_file(chat.id, message.media, caption=new_text)
                    else:
                        await client.send_message(chat.id, new_text)
                except Exception as e:
                    print(f"Error in sending message to chat {chat.id}: {e}")
        try:
            cycle_sleep = int(str(wait_str).split('-')[0]) if '-' in str(wait_str) else int(wait_str)
        except:
            cycle_sleep = 10
        await asyncio.sleep(cycle_sleep)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.نشر_كروبات (\S+)$"))
async def nshr_groups_handler(event):
    await event.delete()
    wait_str = event.pattern_match.group(1)
    message = await event.get_reply_message()
    if not message:
        return await event.respond("يجب الرد على رسالة لاستخدام هذا الأمر.")
    
    global publish_active
    publish_active = True
    await auto_post_groups(client, wait_str, message)

super_groups = ["super", "سوبر"]

async def auto_post_super(client, wait_str, message):
    global publish_active
    publish_active = True
    all_chats = await client.get_dialogs()
    while publish_active:
        for chat in all_chats:
            if not publish_active:
                break
            chat_title_lower = chat.title.lower()
            if chat.is_group and any(keyword in chat_title_lower for keyword in super_groups):
                sleep_time, new_text = get_sleep_and_text(wait_str, message.text)
                try:
                    if message.media:
                        await client.send_file(chat.id, message.media, caption=new_text)
                    else:
                        await client.send_message(chat.id, new_text)
                except Exception as e:
                    print(f"Error in sending message to chat {chat.id}: {e}")
        try:
            cycle_sleep = int(str(wait_str).split('-')[0]) if '-' in str(wait_str) else int(wait_str)
        except:
            cycle_sleep = 10
        await asyncio.sleep(cycle_sleep)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.سوبر (\S+)$"))
async def nshr_super_handler(event):
    await event.delete()
    wait_str = event.pattern_match.group(1)
    message = await event.get_reply_message()
    if not message:
        return await event.respond("يجب الرد على رسالة.")
    
    global publish_active
    publish_active = True
    await auto_post_super(client, wait_str, message)

@client.on(events.NewMessage(func=is_allowed, pattern='.ايقاف النشر'))
async def stop_posting(event):
    global publish_active
    publish_active = False
    await event.respond("** ︙ تم ايقاف النشر التلقائي بنجاح ✓  ** ")

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.(الاوامر|فحص|م1|م2|م3|م4)$"))
async def commands_handler(event):
    await event.delete()
    if event.pattern_match.group(1) == "م1":
        commands_list = """**
   قـائمة اوامر النشر التلقائي 

==================

`.نشر` عدد الثواني معرف الكروب :
 - للنشر في المجموعة التي وضعت معرفها مع عدد الثواني

`.نشر_كروبات` عدد الثواني : 
- للنشر في جميع المجموعات الموجوده في حسابك
 
`.سوبر` عدد الثواني : 
- للنشر بكافة المجموعات السوبر التي منظم اليها 

`.تناوب` عدد الثواني : 
- للنشر في جميع المجموعات بالتناوب وحسب الوقت المحدد 

`.خاص` : 
- للنشر في جميع المحادثات الخاصة مرة واحدة فقط

`.نقط` عدد الثواني : 
- للرد على نفس الرسالة ب (.) وحسب الوقت المحدد 

`.مكرر` عدد الثواني : 
- لتكرار نفس الرسالة وحسب الوقت المحدد 

`.سبام` : 
- يرسل الجملة حرف بعد حرف الى ان تنتهي الجملة .

`.وسبام` :
- يرسل الجملة كلمة بعد كلمة

`.ايقاف النشر` :
- لأيقاف جميع انواع النشر اعلاه


• مُـلاحظة 1 : جميع الأوامر اعلاه تستخدم بالرد على الرسالة او الكليشة المُراد نشرها.
• مُـلاحظة 2 : جميع الأوامر اعلاه تستقبل صورة واحدة موصوفة بنص وليس اكثر من ذلك.
• مُـلاحظة 3 (الحماية الفائقة) : يمكنك إرسال الوقت كنطاق (مثال: 10-20) بدلاً من رقم ثابت.
    **"""
        await event.respond(message=commands_list)
    elif event.pattern_match.group(1) == "فحص":
        start_time = time.time()
        msg = await event.respond("جاري الفحص...")
        end_time = time.time()
        ping = round((end_time - start_time) * 1000, 2)
        check_msg = f"**سورس النشر التلقائي يعمل بنجاح ✅**\n**السرعة (Ping):** `{ping} ms`\nلعرض قائمة الاوامر أرسل `.الاوامر`"
        await msg.edit(check_msg)
    elif event.pattern_match.group(1) == "الاوامر":
        main_menu = """
        ⋆┄─┄الاوامر─┄┄⋆
       ` .م1 ` ➪ اوامــر النشــر التلقــائي
       ` .م2 ` ➪ اوامــر الـذاتيــة
       ` .م3 ` ➪ اوامــر الرد التلقائي (خاص)
       ` .م4 ` ➪ اوامــر مجموعة التخزين
        ⋆┄─┄─┄─┄┄⋆
"""
        await event.respond(message=main_menu)
    elif event.pattern_match.group(1) == "م2":
        self_media_cmds = """
        ~ .ذاتية
يستخدم لحفظ الصور والفيديوهات المؤقتة (بالرد على الصورة).

       ~ .حفظ الذاتية
سيقوم هذا الامر بعد تفعيلة بحفظ الصور والفيديوهات المؤقته تلقائيا .
"""
        await event.respond(message=self_media_cmds)
    elif event.pattern_match.group(1) == "م3":
        m3_cmds = """**
        قائمة الرد التلقائي للخاص :
        
        `.تعيين الرد` + النص : لتعيين رسالة رد تلقائي.
        `.ايقاف الرد` : لإيقاف الرد التلقائي.
        
        - يرد البوت على كل شخص في الخاص مرة واحدة كل 5 دقائق لتجنب الازعاج.
        **"""
        await event.respond(message=m3_cmds)
    elif event.pattern_match.group(1) == "م4":
        m4_cmds = """**
        قائمة مجموعة التخزين (Log Group) :
        
        `.تعيين التخزين` : أرسل هذا الأمر داخل المجموعة التي تريد حفظ الرسائل فيها.
        `.الغاء التخزين` : لإلغاء تحويل الرسائل.
        **"""
        await event.respond(message=m4_cmds)

from os import remove

auto_save_enabled = False

@client.on(events.NewMessage(func=is_allowed, pattern=r'\.واو|\.حفظ الذاتية|\.ذاتية'))
async def rundrc(event):
    await event.delete()
    if event.pattern_match.group(0) == ".ذاتية":
        try:
            getrestrictedcontent = await event.get_reply_message()
            downloadrestrictedcontent = await getrestrictedcontent.download_media()
            await event.client.send_file("me", downloadrestrictedcontent)
            remove(downloadrestrictedcontent)
        except:
            pass
    elif event.pattern_match.group(0) == ".حفظ الذاتية":
        global auto_save_enabled
        auto_save_enabled = not auto_save_enabled
        if auto_save_enabled:
            await event.respond("تم تفعيل حفظ الوسائط ذاتية التدمير تلقائيًا.")
        else:
            await event.respond("تم إيقاف حفظ الوسائط ذاتية التدمير تلقائيًا.")

@client.on(events.NewMessage)
async def auto_save_media(event):
    if auto_save_enabled:
        try:
            if event.media and event.media.ttl_seconds:
                downloadrestrictedcontent = await event.download_media()
                await event.client.send_file("me", downloadrestrictedcontent)
                remove(downloadrestrictedcontent)
        except:
            pass

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.سبام$"))
async def char_spam_handler(event):
    await event.delete()
    message = await event.get_reply_message()
    if not message or not message.text:
        return await event.respond("يجب الرد على رسالة نصية لاستخدام هذا الأمر.")

    for char in message.text:
        if char.strip():
            await event.respond(char)
            await asyncio.sleep(0.5)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.وسبام$"))
async def word_spam_handler(event):
    await event.delete()
    message = await event.get_reply_message()
    if not message or not message.text:
        return await event.respond("يجب الرد على رسالة نصية لاستخدام هذا الأمر.")

    words = message.text.split()
    for word in words:
        await event.respond(word)
        await asyncio.sleep(1)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.تناوب (\S+)$"))
async def rotate_handler(event):
    await event.delete()
    wait_str = event.pattern_match.group(1)
    message = await event.get_reply_message()
    if not message:
        return await event.respond("يجب الرد على رسالة لاستخدام هذا الأمر.")

    global publish_active
    publish_active = True
    chats = await client.get_dialogs()
    groups = [chat for chat in chats if chat.is_group]
    num_groups = len(groups)
    if num_groups == 0:
        return
    current_group_index = 0

    while publish_active:
        sleep_time, new_text = get_sleep_and_text(wait_str, message.text)
        try:
            if message.media:
                await client.send_file(groups[current_group_index].id, message.media, caption=new_text)
            else:
                await client.send_message(groups[current_group_index].id, new_text)
        except Exception as e:
            print(f"Error in sending message to chat {groups[current_group_index].id}: {e}")

        current_group_index = (current_group_index + 1) % num_groups
        await asyncio.sleep(sleep_time)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.خاص$"))
async def private_handler(event):
    await event.delete()
    message = await event.get_reply_message()
    if not message:
        return await event.respond("يجب الرد على رسالة لاستخدام هذا الأمر.")

    chats = await client.get_dialogs()
    private_chats = [chat for chat in chats if chat.is_user]

    for chat in private_chats:
        try:
            if message.media:
                await client.send_file(chat.id, message.media, caption=message.text)
            else:
                await client.send_message(chat.id, message.text)
        except Exception as e:
            print(f"Error in sending message to chat {chat.id}: {e}")

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.نقط (\S+)$"))
async def dot_handler(event):
    await event.delete()
    wait_str = event.pattern_match.group(1)
    try:
        seconds = int(wait_str)
    except:
        seconds = 10
    reply_to_msg = await event.get_reply_message()
    if not reply_to_msg:
        return await event.respond("يجب الرد على رسالة لاستخدام هذا الأمر.")

    global publish_active
    publish_active = True

    while publish_active:
        await reply_to_msg.reply(".")
        await asyncio.sleep(seconds)

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.مكرر (\S+)$"))
async def repeat_handler(event):
    await event.delete()
    wait_str = event.pattern_match.group(1)
    try:
        seconds = int(wait_str)
    except:
        seconds = 10
    message = await event.get_reply_message()
    if not message:
        return await event.respond("يجب الرد على رسالة لاستخدام هذا الأمر.")

    global publish_active
    publish_active = True

    while publish_active:
        await message.respond(message)
        await asyncio.sleep(seconds)

# ==========================================
# أوامر الرد التلقائي (م3)
# ==========================================
@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.تعيين الرد (.+)$"))
async def set_auto_reply(event):
    global auto_reply_text, auto_reply_enabled
    auto_reply_text = event.pattern_match.group(1)
    auto_reply_enabled = True
    await event.respond(f"**تم تعيين الرد التلقائي بنجاح وتفعيله:**\n`{auto_reply_text}`")

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.ايقاف الرد$"))
async def stop_auto_reply(event):
    global auto_reply_enabled
    auto_reply_enabled = False
    await event.respond("**تم إيقاف الرد التلقائي.**")

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def auto_reply_handler(event):
    global auto_reply_enabled, auto_reply_text, auto_reply_cache
    
    if not auto_reply_enabled or not auto_reply_text:
        return
        
    me = await client.get_me()
    if event.sender_id == me.id:
        return

    sender_id = event.sender_id
    now = datetime.now()
    last_reply = auto_reply_cache.get(sender_id)
    
    if last_reply:
        diff = (now - last_reply).total_seconds() / 60
        if diff < 5: 
            return
            
    auto_reply_cache[sender_id] = now
    await asyncio.sleep(random.randint(2, 5))
    try:
        await event.reply(auto_reply_text)
    except:
        pass

# ==========================================
# أوامر التخزين (م4)
# ==========================================
@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.تعيين التخزين$"))
async def set_log_group_cmd(event):
    global log_group_id
    log_group_id = event.chat_id
    await event.respond("**✅ تم تعيين هذه المجموعة كجهة تخزين للرسائل.**")

@client.on(events.NewMessage(func=is_allowed, pattern=r"^\.الغاء التخزين$"))
async def clear_log_group_cmd(event):
    global log_group_id
    log_group_id = None
    await event.respond("**✅ تم إلغاء التخزين بنجاح.**")

@client.on(events.NewMessage(incoming=True))
async def log_messages_handler(event):
    global log_group_id
    if not log_group_id:
        return

    me = await client.get_me()
    if event.sender_id == me.id:
        return

    if not event.is_private and not event.mentioned:
        return

    is_ttl = False
    if event.media:
        if hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds: 
            is_ttl = True
        elif hasattr(event.media, 'photo') and hasattr(event.media.photo, 'ttl_seconds'): 
            is_ttl = True

    try:
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', 'Unknown')
        sender_id = sender.id
        sender_user = f"@{sender.username}" if getattr(sender, 'username', None) else "لا يوجد"
        
        chat_title = "الخاص 🔒" if event.is_private else getattr(await event.get_chat(), 'title', 'مجموعة')
        
        log_text = f"🔔 **تنبيه جديد**\n"
        log_text += f"👤 **الاسم:** {sender_name} (`{sender_id}`)\n"
        log_text += f"🔖 **المعرف:** {sender_user}\n"
        log_text += f"📍 **المصدر:** {chat_title}\n"
        
        if is_ttl:
            path = await event.download_media()
            if path:
                await client.send_file(log_group_id, path, caption=log_text + "\n🔥 **ميديا ذاتية التدمير!**")
                os.remove(path)
            else:
                await client.send_message(log_group_id, log_text + "\n(فشل التحميل)")
        else:
            await client.forward_messages(log_group_id, event.message)
            await client.send_message(log_group_id, log_text, link_preview=False)
    except Exception as e:
        print(f"Log Error: {e}")

print('تم تشغيل سورس النشر التلقائي بنجاح')
client.run_until_disconnected()
