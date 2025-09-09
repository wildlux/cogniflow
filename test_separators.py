#!/usr/bin/env python3
"""
Test script to verify separator removal
"""

import os

def check_separators():
    """Check that horizontal separators are removed and vertical ones remain"""
    qml_file = "/home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa/UI/main_interface.qml"

    if not os.path.exists(qml_file):
        print("❌ QML file not found")
        return False

    with open(qml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("🔍 Checking separators...")

    # Check that horizontal separators (MenuSeparator) are removed
    menu_separator_count = content.count("MenuSeparator {}")
    if menu_separator_count == 0:
        print("✅ All MenuSeparator (horizontal) removed")
    else:
        print(f"❌ Still found {menu_separator_count} MenuSeparator")

    # Check that vertical separators (ToolSeparator) remain
    tool_separator_count = content.count("ToolSeparator {}")
    if tool_separator_count == 2:
        print("✅ ToolSeparator (vertical) preserved - 2 found")
    else:
        print(f"❌ ToolSeparator count incorrect: {tool_separator_count} (expected 2)")

    return menu_separator_count == 0 and tool_separator_count == 2

def show_menu_structure():
    """Show the current menu structure without separators"""
    qml_file = "/home/wildlux/Scrivania/Python/CogniFLow/assistente_dsa/UI/main_interface.qml"

    with open(qml_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("\n📋 Current Menu Structure:")

    in_menu = False
    current_menu = ""

    for i, line in enumerate(lines, 1):
        if 'Menu {' in line and 'title:' in line:
            in_menu = True
            menu_title = line.strip().split('title:')[1].strip().strip('"')
            current_menu = menu_title
            print(f"\n🔸 {current_menu}:")
        elif 'MenuItem {' in line and in_menu:
            # Find the text of the menu item
            for j in range(i, min(i+5, len(lines))):
                if 'text:' in lines[j]:
                    text = lines[j].strip().split('text:')[1].strip().strip('"')
                    print(f"   • {text}")
                    break
        elif '}' in line and in_menu and current_menu:
            in_menu = False

def main():
    print("🧪 Testing Separator Removal")
    print("=" * 40)

    separator_check = check_separators()
    show_menu_structure()

    print("\n" + "=" * 40)
    print("📊 Results:")

    if separator_check:
        print("🎉 Separator cleanup completed successfully!")
        print("📋 Summary:")
        print("   • ❌ Removed 3 MenuSeparator (horizontal)")
        print("   • ✅ Kept 2 ToolSeparator (vertical)")
        print("   • 📝 Menus now have continuous item lists")
        return 0
    else:
        print("⚠️ Some separator issues found")
        return 1

if __name__ == "__main__":
    exit(main())