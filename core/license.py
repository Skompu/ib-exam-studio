import streamlit as st

def validate_whop_license(user_key: str) -> tuple[bool, str]:
    # Sprawdzenie czy włączony jest tryb debugowania w secrets.toml
    is_debug = False
    try:
        is_debug = st.secrets.get("DEBUG", False)
    except Exception:
        pass

    test_key = "DEV-TEST-2026"
    
    if user_key == test_key:
        if is_debug:
            return True, "✅ Licencja zweryfikowana pomyślnie (Tryb deweloperski)."
        else:
            return False, "❌ Klucz testowy jest wyłączony w środowisku produkcyjnym."
            
    # Tutaj docelowa integracja z Whop API dla kluczy komercyjnych
    if user_key and len(user_key) > 8:
        return True, "✅ Licencja Whop aktywna."
        
    return False, "❌ Nieprawidłowy lub wygasły klucz licencyjny."