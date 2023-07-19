from bot.db.supabase import supabase


async def fetch_by_id(user_id, column_name):
    response = supabase.table('tg_ban_bot_games').select(column_name).eq('id', user_id).execute()

    if response.data:
        return response.data[0][column_name]
    else:
        return None


async def fetch_multiple_params(user_id, *columns):
    response = supabase.table('tg_ban_bot_games').select(*columns).eq('id', user_id).execute()

    if response.data:
        return response.data[0].values()
    else:
        return None
