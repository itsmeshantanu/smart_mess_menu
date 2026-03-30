"""
Run: python seed_menu_31.py
Adds menus for ALL messes on 31-03-2026
Deletes old menus for that date and recreates fresh ones
"""

import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_mess.settings')
django.setup()

from mess.models import Mess, Menu, Dish

TARGET_DATE = datetime.date(2026, 3, 31)

print("🌱 Seeding menus for 31-03-2026...")

# ── DATA (Option C: different per mess) ──────────────────────────────────────
MESS_MENU_DATA = {
    "Shree Sai Mess": {
        "general": ["Dal Rice", "Roti", "Sabzi", "Papad", "Salad"],
        "lunch": ["Paneer Butter Masala", "Jeera Rice", "Dal Tadka", "Roti", "Raita"],
        "dinner": ["Chole Bhature", "Mixed Veg", "Dal Makhani", "Roti", "Pickle"],
    },
    "Annapurna Bhojanalaya": {
        "general": ["Poha", "Upma", "Tea", "Bread Butter"],
        "lunch": ["Rajma Chawal", "Aloo Gobi", "Dal Fry", "Roti", "Buttermilk"],
        "dinner": ["Palak Paneer", "Plain Rice", "Dal", "Roti", "Salad"],
    },
    "Maa ka Dhaba": {
        "general": ["Paratha", "Curd", "Tea", "Pickle"],
        "lunch": ["Veg Biryani", "Raita", "Papad", "Salad"],
        "dinner": ["Dal Tadka", "Rice", "Roti", "Sabzi", "Pickle"],
    },
    "Metro dinning": {
        "general": ["Sandwich", "Tea", "Coffee", "Biscuits"],
        "lunch": ["Veg Pulao", "Paneer Curry", "Roti", "Dal", "Salad"],
        "dinner": ["Fried Rice", "Manchurian", "Noodles", "Soup"],
    },
    "Aapli Awad": {
        "general": ["Misal Pav", "Tea", "Poha"],
        "lunch": ["Pithla Bhakri", "Rice", "Dal", "Sabzi", "Thecha"],
        "dinner": ["Zunka Bhakri", "Rice", "Dal", "Pickle"],
    },
    "swarajya": {
        "general": ["Idli", "Sambar", "Tea"],
        "lunch": ["Sambar Rice", "Poriyal", "Curd", "Papad"],
        "dinner": ["Dosa", "Chutney", "Sambar", "Upma"],
    },
}

# ── MAIN LOOP ────────────────────────────────────────────────────────────────
for mess in Mess.objects.all():

    if mess.name not in MESS_MENU_DATA:
        print(f"  ⏭ Skipping {mess.name} (no data provided)")
        continue

    print(f"\n  🔧 Processing: {mess.name}")

    data = MESS_MENU_DATA[mess.name]

    # 🔥 DELETE OLD MENUS FOR THAT DATE (LUNCH + DINNER)
    Menu.objects.filter(mess=mess, date=TARGET_DATE).delete()

    # 🔥 DELETE GENERAL MENU (date=None)
    Menu.objects.filter(mess=mess, menu_type='GENERAL', date=None).delete()

    # ── CREATE GENERAL ───────────────────────────────────────────────────────
    g_menu = Menu.objects.create(
        mess=mess,
        menu_type='GENERAL',
        date=None
    )
    for dish in data["general"]:
        Dish.objects.create(menu=g_menu, name=dish)

    # ── CREATE LUNCH ─────────────────────────────────────────────────────────
    l_menu = Menu.objects.create(
        mess=mess,
        menu_type='LUNCH',
        date=TARGET_DATE
    )
    for dish in data["lunch"]:
        Dish.objects.create(menu=l_menu, name=dish)

    # ── CREATE DINNER ────────────────────────────────────────────────────────
    d_menu = Menu.objects.create(
        mess=mess,
        menu_type='DINNER',
        date=TARGET_DATE
    )
    for dish in data["dinner"]:
        Dish.objects.create(menu=d_menu, name=dish)

    print(f"  ✅ Menus added for {mess.name}")

print("\n✅ Done seeding menus for 31-03-2026")