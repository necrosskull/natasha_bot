import bot.db.supabase as supabase

supabase = supabase.Supabase()


async def fetch_by_id(user_id, column_name):
    data = await supabase.table('tg_ban_bot_games').select(column_name).eq('id', user_id).execute()

    if data:
        return data[0][column_name]
    else:
        return None
