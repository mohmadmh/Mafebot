# أضف هذا المتغير لتخزين الأصوات
votes_count = {}
voted_players = []

async def start_voting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # التأكد أن المطور هو من يبدأ التصويت أو النظام تلقائياً
    if not is_developer(query.from_user):
        await query.answer("هذا الأمر للمطور فقط حالياً! 🛡️", show_alert=True)
        return

    votes_count.clear()
    voted_players.clear()

    # إنشاء أزرار بأسماء جميع اللاعبين المنضمين
    keyboard = []
    for uid, name in players_list.items():
        keyboard.append([InlineKeyboardButton(f"التصويت ضد {name} 💀", callback_data=f"v_{uid}")])
    
    await query.message.reply_text(
        "📢 **بدأ وقت التصويت العام!**\n\nتحدثوا في المجموعة وقرروا من هو المافيا، ثم اضغط على الاسم أدناه لإقصائه.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def register_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    voter_id = query.from_user.id
    target_id = query.data.split("_")[1] # استخراج ID الشخص المستهدف

    # منع التصويت المكرر
    if voter_id in voted_players:
        await query.answer("لقد صوتّ بالفعل! لا يمكنك التلاعب بالأصوات. 🚫", show_alert=True)
        return

    # تسجيل الصوت
    target_id = int(target_id)
    votes_count[target_id] = votes_count.get(target_id, 0) + 1
    voted_players.append(voter_id)

    await query.answer(f"تم تسجيل صوتك ضد {players_list[target_id]} ✅")

    # إذا صوت الجميع، نعلن النتيجة (أو يمكن للمطور إنهاء التصويت يدوياً)
    if len(voted_players) >= len(players_list):
        await finish_voting(query, context)

async def finish_voting(query, context):
    if not votes_count:
        await query.message.reply_text("🏁 انتهى الوقت ولم يصوت أحد!")
        return

    # معرفة من حصل على أعلى أصوات
    winner_id = max(votes_count, key=votes_count.get)
    winner_name = players_list[winner_id]
    
    await query.message.reply_text(
        f"🏁 **انتهى التصويت!**\n\nالضحية هي: **{winner_name}** 💀\nبمجموع أصوات: {votes_count[winner_id]}"
    )
    
    # إخراج اللاعب من القائمة
    del players_list[winner_id]
    
    # إعطاء المطور خيار بدء جولة جديدة أو إنهاء اللعبة
    if is_developer(query.from_user):
        await query.message.reply_text(
            "🛠 **تحكم المطور:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("جولة تصويت جديدة 🔄", callback_data="start_vote")],
                [InlineKeyboardButton("إنهاء اللعبة 🔚", callback_data="reset_game")]
            ])
        )

# تحديث المعالجات (Handlers) في نهاية الملف
application.add_handler(CallbackQueryHandler(start_voting, pattern="start_vote"))
application.add_handler(CallbackQueryHandler(register_vote, pattern="^v_"))
