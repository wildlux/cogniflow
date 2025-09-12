#!/usr/bin/env python3
"""
Test script to verify menu renaming
"""

import os

def check_menu_names():
    """Check that menu names have been updated correctly"""
    qml_file = "/home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa/UI/main_interface.qml"

    if not os.path.exists(qml_file):
        print("❌ QML file not found")
        return False

    with open(qml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for new menu names
    new_menus = [
        'title: "📝 Documenti"',
        'title: "🎯 Operazioni"',
        'title: "⚙️ Configurazione"',
        'title: "📚 Guida"'
    ]

    # Check for old menu names (should not exist)
    old_menus = [
        'title: "📁 File"',
        'title: "⚙️ Strumenti"',
        'title: "🔧 Opzioni"',
        'title: "❓ Aiuto"'
    ]

    print("🔍 Checking menu names...")

    all_new_present = True
    for menu in new_menus:
        if menu in content:
            print(f"✅ Found: {menu}")
        else:
            print(f"❌ Missing: {menu}")
            all_new_present = False

    no_old_present = True
    for menu in old_menus:
        if menu in content:
            print(f"❌ Still found old menu: {menu}")
            no_old_present = False

    if no_old_present:
        print("✅ No old menu names found")

    return all_new_present and no_old_present

def check_log_references():
    """Check that log messages reference the new menu name"""
    files_to_check = [
        "/home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa/UI/main_interface.qml",
        "/home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa/UI/components/LogPanel.qml",
        "/home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa/UI/js/log_functions.js"
    ]

    print("\n🔍 Checking log message references...")

    all_updated = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            filename = os.path.basename(file_path)

            # Check for new reference
            if 'menu Operazioni' in content:
                print(f"✅ {filename}: Found 'menu Operazioni'")
            else:
                print(f"❌ {filename}: Missing 'menu Operazioni'")
                all_updated = False

            # Check for old reference (should not exist)
            if 'menu Strumenti' in content:
                print(f"❌ {filename}: Still has 'menu Strumenti'")
                all_updated = False

    return all_updated

def main():
    print("🧪 Testing Menu Renaming")
    print("=" * 40)

    menu_check = check_menu_names()
    log_check = check_log_references()

    print("\n" + "=" * 40)
    print("📊 Results:")

    if menu_check and log_check:
        print("🎉 Menu renaming completed successfully!")
        print("📋 Changes made:")
        print("   • 📁 File → 📝 Documenti")
        print("   • ⚙️ Strumenti → 🎯 Operazioni")
        print("   • 🔧 Opzioni → ⚙️ Configurazione")
        print("   • ❓ Aiuto → 📚 Guida")
        print("   • Updated all log message references")
        return 0
    else:
        print("⚠️ Some menu renaming issues found")
        return 1

if __name__ == "__main__":
    exit(main())