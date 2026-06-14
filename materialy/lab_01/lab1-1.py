from functools import wraps

current_user = {"username": "admin", "role": "superuser"}

def require_role(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.get("role") != role:
                raise PermissionError(
                    f"Wymagana rola '{role}', a użytkownik ma '{current_user.get('role')}'"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


@require_role("superuser")
def delete_database():
    return "Baza danych usunięta"


@require_role("admin")
def view_logs():
    return "Logi: ..."


print(delete_database())   # OK — rola superuser
print(view_logs())         # PermissionError — wymaga admin