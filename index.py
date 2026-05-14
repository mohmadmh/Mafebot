async def handle_callback(update: Update, context):
    query = update.callback_query
    user = query.from_user
    
    # 1. منطق الانضمام
    if query.data == "join":
        if user.id not in players:
            players[user.id] = {"name": user.first_name, "username": user.username}
            await query.message.reply_text(f"👤 انضم اللاعب: {user.first_name}")
            
            # إذا كان الشخص الذي انضم هو المطور @H0_Om، نظهر له زر البدء
            if user.username == DEV_USER:
                keyboard = [[InlineKeyboardButton("🚀 ابدأ اللعبة الآن", callback_data="start_game")]]
                await query.message.reply_text(
                    f"أهلاً مطور {user.first_name}، عندما يكتمل العدد اضغط على البدء:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await query.answer("أنت منضم بالفعل! ⚠️")
        await query.answer()

    # 2. منطق بدء اللعبة (للمطور فقط)
    elif query.data == "start_game":
        if user.username != DEV_USER:
            await query.answer("عذراً، المطور @H0_Om هو الوحيد المخول ببدء اللعبة! 🚫", show_alert=True)
            return

        if len(players) < 3:
            await query.answer("يجب انضمام 3 لاعبين على الأقل للبدء! 👥", show_alert=True)
            return

        # توزيع الأدوار
        uids = list(players.keys())
        roles = ["مافيا 🔪", "طبيب 💊", "محقق 🔍"] + ["مواطن 👨‍🌾"] * (len(uids) - 3)
        random.shuffle(roles)

        for i, uid in enumerate(uids):
            role = roles[i]
            try:
                await context.bot.send_message(chat_id=uid, text=f"🕵️ دورك السري هو: {role}")
            except:
                pass 

        await query.edit_message_text("✅ تم توزيع الأدوار سراً على جميع اللاعبين!\nبدأت اللعبة الآن.. تحدثوا في المجموعة.")
        await query.answer()
