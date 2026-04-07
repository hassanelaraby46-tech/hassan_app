import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import io

# إعداد الصفحة
st.set_page_config(page_title="Schedule Smart", page_icon="📅", layout="centered")

# تصحيح الجزء الخاص بالتنسيق (CSS)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1F4E78; color: white; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; }
    </style>
    """, unsafe_allow_html=True) # تم تعديل هذا السطر هنا

st.title("📅 Schedule Smart v1.4")
st.write("نسخة الموبايل - نظام توزيع الورديات الذكي")

# --- مدخلات المستخدم ---
with st.expander("👥 إعداد الموظفين والأنماط", expanded=True):
    names_input = st.text_area("Staff Names (Separate by comma):", 
                              "Mohamed, Ali, Ahmed, Hassan, Sayed, Yassin, Osama")
    
    patterns_input = st.text_area("Individual Patterns (Separate each by | ):", 
                                 "M,L,L,N,N,O,O | M,L,L,N,N,O,O | M,L,L,N,N,O,O")

with st.expander("📅 اختيار التاريخ", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("الشهر", list(range(1, 13)), index=datetime.now().month - 1)
    with col2:
        year = st.selectbox("السنة", [2025, 2026, 2027], index=1)

# --- معالجة البيانات وإنشاء الملف ---
if st.button("🚀 إنشاء الجدول الاحترافي"):
    try:
        names = [n.strip() for n in names_input.split(",") if n.strip()]
        patterns_raw = [p.strip().upper() for p in patterns_input.split("|") if p.strip()]

        if len(names) != len(patterns_raw):
            st.error(f"⚠️ خطأ: عدد الأسماء ({len(names)}) لا يطابق عدد الأنماط ({len(patterns_raw)})!")
        else:
            num_days = calendar.monthrange(year, month)[1]
            dates = pd.date_range(start=f"{year}-{month}-01", periods=num_days)
            
            data = []
            headers = ["Date", "Day"] + names
            for d_idx in range(num_days):
                row = [dates[d_idx].strftime('%d-%m-%Y'), dates[d_idx].day_name()]
                for p_idx, p_str in enumerate(patterns_raw):
                    p_list = [s.strip() for s in p_str.split(",")]
                    row.append(p_list[d_idx % len(p_list)])
                data.append(row)
            
            df = pd.DataFrame(data, columns=headers)

            # إنشاء ملف الإكسيل في الذاكرة بنفس تنسيقاتك السابقة
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Nursing_Shifts', startrow=1)
                workbook = writer.book
                worksheet = writer.sheets['Nursing_Shifts']

                # تنسيق العناوين والألوان
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#002060', 'font_color': 'white', 'border': 2, 'align': 'center'})
                worksheet.set_column(0, 1, 15)
                worksheet.set_column(2, len(headers)-1, 18)

                colors_map = {'M': '#92D050', 'L': '#FFC000', 'N': '#FF0000', 'O': '#D9D9D9'}
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(1, col_num, value, header_fmt)

                for key, color in colors_map.items():
                    fmt = workbook.add_format({'bg_color': color, 'border': 1, 'align': 'center', 'bold': True})
                    if key == 'N': fmt.set_font_color('white')
                    worksheet.conditional_format(2, 2, num_days+1, len(headers)-1, 
                                               {'type': 'text', 'criteria': 'containing', 'value': key, 'format': fmt})

                worksheet.freeze_panes(2, 2)

            st.success("✅ تم إنشاء الملف بنجاح!")
            
            st.download_button(
                label="📥 تحميل ملف الإكسيل",
                data=output.getvalue(),
                file_name=f"ScheduleSmart_{month}_{year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.write("### معاينة الجدول:")
            st.dataframe(df)

    except Exception as e:
        st.error(f"حدث خطأ غير متوقع: {e}")

st.info("💡 ملاحظة: لكل فرد نمط خاص، افصل بين الأنماط باستخدام العلامة |")