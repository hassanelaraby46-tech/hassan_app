import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import io

st.set_page_config(page_title="Schedule Smart v1.7", page_icon="📊", layout="wide")

# --- دالة حساب الإحصائيات (تلقائية عند التعديل) ---
def calculate_stats(df, names):
    stats = []
    for name in names:
        # حساب التكرارات لكل ممرض من الجدول (سواء الأصلي أو المعدل)
        shifts = df[name].value_counts()
        m_count = shifts.get('M', 0)
        l_count = shifts.get('L', 0)
        n_count = shifts.get('N', 0)
        o_count = shifts.get('O', 0)
        
        # الحساب: M=6h, L=12h, N=12h
        total_hours = (m_count * 6) + (l_count * 12) + (n_count * 12)
        total_shifts = m_count + l_count + n_count
        
        stats.append({
            "الممرض": name,
            "M (6h)": m_count,
            "L (12h)": l_count,
            "N (12h)": n_count,
            "ساعات العمل": total_hours,
            "إجمالي الشفتات": total_shifts
        })
    return pd.DataFrame(stats)

st.title("📊 Schedule Smart v1.7")
st.info("💡 يمكنك الآن التعديل مباشرة داخل الجدول وسيقوم البرنامج بإعادة حساب الساعات فوراً!")

# --- المدخلات ---
with st.sidebar:
    st.header("⚙️ إعدادات الجدول")
    names_input = st.text_area("أسماء الطاقم (فواصل):", "Mohamed, Ali, Ahmed")
    patterns_input = st.text_area("الأنماط (فاصلة |):", "M,L,N,O | M,L,N,O | M,L,N,O")
    
    col1, col2 = st.columns(2)
    month = col1.selectbox("الشهر", list(range(1, 13)), index=datetime.now().month - 1)
    year = col2.selectbox("السنة", [2025, 2026, 2027], index=1)

# --- معالجة البيانات ---
names = [n.strip() for n in names_input.split(",") if n.strip()]
patterns_raw = [p.strip().upper() for p in patterns_input.split("|") if p.strip()]

if len(names) == len(patterns_raw) and names:
    num_days = calendar.monthrange(year, month)[1]
    dates = pd.date_range(start=f"{year}-{month}-01", periods=num_days)
    
    # 1. توليد البيانات الأولية
    initial_data = []
    for d_idx in range(num_days):
        row = {"Date": dates[d_idx].strftime('%d-%m'), "Day": dates[d_idx].day_name()[:3]}
        for p_idx, name in enumerate(names):
            p_list = [s.strip() for s in patterns_raw[p_idx].split(",")]
            row[name] = p_list[d_idx % len(p_list)]
        initial_data.append(row)
    
    df_initial = pd.DataFrame(initial_data)

    # 2. ميزة التعديل الذاتي (Data Editor)
    st.write("### 📝 جدول الورديات (اضغط على أي خانة للتعديل)")
    # هذا المكون يسمح للمستخدم بتغيير القيم يدوياً
    df_edited = st.data_editor(df_initial, use_container_width=True, hide_index=True)

    # 3. حساب الإحصائيات بناءً على الجدول المعدل
    st.write("### 📈 إحصائيات الساعات المحدثة")
    df_stats = calculate_stats(df_edited, names)
    st.table(df_stats)

    # --- تصدير الإكسيل ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_edited.to_excel(writer, sheet_name='Roster', index=False)
        df_stats.to_excel(writer, sheet_name='Stats', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Roster']
        # تنسيق الألوان للأرقام والحروف
        colors = {'M': '#92D050', 'L': '#FFC000', 'N': '#FF0000', 'O': '#D9D9D9'}
        for key, color in colors.items():
            fmt = workbook.add_format({'bg_color': color, 'border': 1})
            worksheet.conditional_format(1, 2, num_days, len(names)+1, 
                                       {'type': 'text', 'criteria': 'containing', 'value': key, 'format': fmt})

    st.download_button("📥 تحميل الجدول النهائي (المعدل يدوياً)", output.getvalue(), 
                       file_name=f"Roster_Updated_{month}.xlsx", mime="application/vnd.ms-excel")
else:
    st.warning("الرجاء التأكد من تطابق عدد الأسماء مع عدد الأنماط.")
