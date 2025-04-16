from backend.db import supabase
from datetime import date

def register(username, password, birthdate, region, phonenumber, gender):
    try:
        result = supabase.table("users").select("login_id").eq("login_id", username).execute()
        if len(result.data) > 0:
            return False  # 이미 존재

        # INSERT
        supabase.table("users").insert({
            "login_id": username,
            "password": password,
            "birthdate": birthdate,
            "regionid": region,
            "phonenumber": phonenumber,
            "gender": gender,
            "last_activity": date.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        print("❌ 회원가입 실패:", e)
        return False

def login(username, password):
    result = supabase.table("users").select("password").eq("login_id", username).execute()
    if len(result.data) == 0:
        return False
    if result.data[0]["password"] == password:
        # 로그인 성공 시 last_activity 업데이트
        today = str(date.today())
        supabase.table("users").update({"last_activity": today}).eq("login_id", username).execute()
        return True
    return False