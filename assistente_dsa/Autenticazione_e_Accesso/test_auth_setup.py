#!/usr/bin/env python3
"""
Test script per verificare il setup dell'autenticazione
"""

from auth_manager import auth_manager

def test_authentication():
    print("🧪 Test Setup Autenticazione DSA Assistant")
    print("=" * 50)

    # Verifica utenti
    print(f"👥 Utenti registrati: {list(auth_manager.users.keys())}")

    # Verifica utente principale
    user_email = 'wildlux@gmail.com'
    if user_email in auth_manager.users:
        user = auth_manager.users[user_email]
        print("✅ Utente principale trovato:")
        print(f"   📧 Email: {user.get('email', 'N/A')}")
        print(f"   👤 Nome: {user.get('full_name', 'N/A')}")
        print(f"   🔑 Gruppo: {user.get('group', 'N/A')}")
        print(f"   ✅ Attivo: {user.get('is_active', False)}")
        print(f"   🔒 Setup richiesto: {user.get('requires_setup', True)}")

        # Test permessi
        permissions = auth_manager.get_user_permissions(user_email)
        print(f"   🔑 Permessi: {permissions}")

        print("\n✅ Setup autenticazione completato con successo!")
        print("📧 Puoi ora utilizzare la tua email personale per accedere al sistema")
        return True
    else:
        print("❌ Utente principale non trovato")
        return False

if __name__ == "__main__":
    test_authentication()