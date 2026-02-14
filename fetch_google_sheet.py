import pandas as pd
import json
import sys
import traceback

MAIN_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRxPqHp5lwwhjdDTaJdiwWYbhqZmeALG5dVhSZ6rHx2W8KGrcNWaa5-7qiVB87KKbQEXjtF1WVwmBzp/pub?gid=50416606&single=true&output=csv"

# DAILY_SALES_URL більше не потрібен - daily.html тепер завантажує дані напряму з Google Sheets

PERCENT_COLUMNS = ['% Доля ACC', 'Доля Послуг', 'Конверсія ПК', 'Конверсія ПК Offline', 'Доля УДС']

def clean_number(value):
    """Надійна очистка чисел від роздільників тисяч та спецсимволів"""
    if pd.isna(value) or value == '': return 0.0
    
    # Перетворюємо в рядок і видаляємо невидимі символи та пробіли
    str_val = str(value).strip().replace('\xa0', '').replace(' ', '')
    
    if not str_val or str_val.lower() in ['nan', 'none']: return 0.0
    
    # Видаляємо символ відсотка
    str_val = str_val.replace('%', '')

    # Логіка обробки ком та крапок:
    # Якщо є і кома, і крапка (напр. 1.234,56)
    if ',' in str_val and '.' in str_val:
        if str_val.find('.') < str_val.find(','): # Європейський формат 1.234,56
            str_val = str_val.replace('.', '').replace(',', '.')
        else: # Американський формат 1,234.56
            str_val = str_val.replace(',', '')
    # Якщо тільки кома
    elif ',' in str_val:
        # Якщо кома одна і після неї 2 знаки — це скоріше десяткова (123,45)
        # Якщо коми розділяють тисячі (1,234,567) — видаляємо їх
        parts = str_val.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            str_val = str_val.replace(',', '.')
        else:
            str_val = str_val.replace(',', '')
            
    try:
        return float(str_val)
    except:
        return 0.0

def process_data():
    try:
        # Завантаження основних даних для вечірнього звіту (index.html)
        print("Завантаження основних даних для вечірнього звіту...")
        df = pd.read_csv(MAIN_SHEET_URL)
        df = df.fillna(0)
        
        gradients = [
            'linear-gradient(135deg, #FF6B6B 0%, #EE5253 100%)', 
            'linear-gradient(135deg, #4834d4 0%, #686de0 100%)', 
            'linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)', 
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
        ]
        
        sales_data = []
        
        # Визначаємо колонки
        cols = df.columns.tolist()
        
        for i, row in df.iterrows():
            name = str(row.iloc[0]).strip()
            # Пропускаємо порожні рядки та підсумки всередині таблиці
            if not name or name.lower() in ['nan', '0', 'разом', 'сума', 'итог']: continue
            
            position = str(row.iloc[1])
            initials = "".join([p[0] for p in name.split()[:2]]).upper()

            metrics = {}
            for col in cols[2:]:
                val = clean_number(row[col])
                unit = '%' if col in PERCENT_COLUMNS else 'грн'
                # Для штук та чеків змінюємо unit
                if col in ['Шт.', 'Чеки', 'ПЧ']: unit = 'шт'
                
                metrics[col] = {'value': val, 'label': col, 'unit': unit}
            
            sales_data.append({
                'id': len(sales_data) + 1,
                'name': name,
                'position': position,
                'initials': initials,
                'gradient': gradients[len(sales_data) % len(gradients)],
                'metrics': metrics
            })

        # Розрахунок загальних показників (МАГ)
        store_totals = {
            'id': 0,
            'name': 'Показники магазину',
            'position': 'Всі продавці',
            'initials': 'ALL', 
            'gradient': 'linear-gradient(135deg, #434343 0%, #000000 100%)',
            'metrics': {}
        }

        # Спочатку рахуємо суми для всіх базових показників (грн, шт)
        for col in cols[2:]:
            vals = [p['metrics'][col]['value'] for p in sales_data]
            unit = '%' if col in PERCENT_COLUMNS else 'грн'
            if col in ['Шт.', 'Чеки', 'ПЧ']: unit = 'шт'
            
            # Для звичайних значень (не відсотків) просто сумуємо
            if col not in PERCENT_COLUMNS:
                res = round(sum(vals), 2)
                store_totals['metrics'][col] = {'value': res, 'label': col, 'unit': unit}

        # Тепер окремо розраховуємо частки (відсотки) для всього магазину
        # Формула: (Сума категорії / Сума ТО) * 100
        
        total_to = store_totals['metrics'].get('ТО', {}).get('value', 0)

        for col in PERCENT_COLUMNS:
            res = 0
            if total_to > 0:
                if col == 'Доля Послуг':
                    # Шукаємо фактичне значення послуг (може називатися 'Послуги грн' або 'Послуги')
                    val_cat = store_totals['metrics'].get('Послуги грн', {}).get('value', 0) or \
                              store_totals['metrics'].get('Послуги', {}).get('value', 0)
                    res = round((val_cat / total_to) * 100, 2)
                
                elif col == '% Доля ACC':
                    val_cat = store_totals['metrics'].get('ACC', {}).get('value', 0)
                    res = round((val_cat / total_to) * 100, 2)
                
                else:
                    # Для інших відсотків (наприклад, Конверсія) залишаємо середнє арифметичне
                    vals = [p['metrics'][col]['value'] for p in sales_data]
                    res = round(sum(vals)/len(vals), 2) if vals else 0
            
            store_totals['metrics'][col] = {'value': res, 'label': col, 'unit': '%'}

        # Збереження тільки sales-data.json (для вечірнього звіту index.html)
        final_json = [store_totals] + sales_data
        with open('sales-data.json', 'w', encoding='utf-8') as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)

        print("✓ sales-data.json успішно оновлений")
        print("ℹ️  daily-sales.json більше не генерується - daily.html завантажує дані напряму з Google Sheets")
        
        # Виводимо статистику
        print(f"\n📊 Оброблено продавців: {len(sales_data)}")
        if total_to > 0:
            print(f"💰 Загальний товарообіг: {total_to:,.2f} грн")

    except Exception as e:
        print(f"❌ Помилка: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    process_data()
