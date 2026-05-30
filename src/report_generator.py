import json
from datetime import datetime
import streamlit as st
from validator import DataValidator


def show_report(project_name, current_active_table, df, rules):
    final_mask, stats = DataValidator.get_error_masks(df, rules)
    total    = df.size
    errors   = final_mask.values.sum()
    accuracy = ((total - errors) / total * 100) if total > 0 else 100

    active_errors = {label: count for label, count in stats.items() if count > 0}

    if active_errors:
        errors_table_rows = ""
        for label, count in active_errors.items():
            error_percentage = (count / errors * 100) if errors > 0 else 0
            errors_table_rows += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">{label}</td>
                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold; text-align: center;">{count}</td>
                <td style="border: 1px solid #ddd; padding: 10px; color: #666; text-align: center;">{error_percentage:.1f}%</td>
            </tr>
            """
    else:
        errors_table_rows = """
        <tr>
            <td colspan="3" style="border: 1px solid #ddd; padding: 15px; text-align: center; color: green; font-weight: bold;">
                Аномалій не виявлено. Дані повністю валідні!
            </td>
        </tr>
        """

    print_html = f"""
    <div style="font-family: Arial, sans-serif; padding: 25px; color: #000; background: #fff;">
        <h1 style="text-align: center; border-bottom: 3px solid #333; padding-bottom: 12px; margin-bottom: 5px;">
            Звіт про якість даних: {project_name}
        </h1>
        <p style="text-align: right; color: #666; font-size: 14px; margin-bottom: 25px;">
            Дата формування: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        </p>

        <h3 style="color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px;">
            Основні метрики таблиці &quot;{current_active_table}&quot;
        </h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 15px;">
            <tr style="background-color: #f8f9fa;">
                <th style="border: 1px solid #ddd; padding: 10px; text-align: left; width: 60%;">Метрика</th>
                <th style="border: 1px solid #ddd; padding: 10px; text-align: center; width: 40%;">Значення</th>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">Рівень якості (Accuracy)</td>
                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold; text-align: center;
                    color: {'#198754' if accuracy > 90 else '#fd7e14'}; font-size: 16px;">
                    {accuracy:.1f}%
                </td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">Загальна кількість комірок (Cells)</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: center; font-weight: bold;">{total}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">Знайдено аномалій</td>
                <td style="border: 1px solid #ddd; padding: 10px; color: #dc3545; font-weight: bold;
                    text-align: center; font-size: 16px;">
                    {int(errors)}
                </td>
            </tr>
        </table>

        <h3 style="color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px;">Детальний аналіз аномалій</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 15px;">
            <tr style="background-color: #f8f9fa;">
                <th style="border: 1px solid #ddd; padding: 10px; text-align: left; width: 50%;">Тип проблеми</th>
                <th style="border: 1px solid #ddd; padding: 10px; text-align: center; width: 25%;">Кількість</th>
                <th style="border: 1px solid #ddd; padding: 10px; text-align: center; width: 25%;">% від усіх помилок</th>
            </tr>
            {errors_table_rows}
        </table>

        <footer style="margin-top: 60px; text-align: center; font-size: 12px; color: #999;
            border-top: 1px solid #ddd; padding-top: 15px;">
            Звіт згенеровано автоматично за допомогою системи DataGuard.
        </footer>
    </div>
    """

    st.components.v1.html(f"""
        <script>
            var htmlContent = {json.dumps(print_html)};
            var printWindow = window.open('', '_blank');
            printWindow.document.write('<html><head><title>DataGuard Report</title></head><body>');
            printWindow.document.write(htmlContent);
            printWindow.document.write('</body></html>');
            printWindow.document.close();
            printWindow.focus();
            setTimeout(function() {{
                printWindow.print();
                printWindow.close();
            }}, 500);
        </script>
    """, height=0)