from __future__ import annotations

import io
import datetime
from decimal import Decimal
from typing import Any, Optional

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

try:
    import qrcode
except ImportError:
    qrcode = None

from taxos.application.documents.chart_renderer import render_chart_to_png


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert hex string (e.g. #FF0000 or FF0000) to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return (0, 0, 0)
    try:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


class PDFDocumentGenerator:
    """Generates professional PDF reports from calculator results using fpdf2."""

    def generate(self, calculator_config: Any, results: dict[str, Any], template: Any, inputs_data: Optional[dict[str, Any]] = None) -> bytes:
        """
        Generate a PDF report.

        Args:
            calculator_config: Configuration of the calculator.
            results: Calculated results dictionary.
            template: Report template configuration.
            inputs_data: Original user inputs.

        Returns:
            PDF file content as bytes.
        """
        if FPDF is None:
            raise RuntimeError("fpdf2 is not installed. Please install it to generate PDFs.")
            
        inputs_data = inputs_data or {}
        
        orientation_attr = getattr(template, 'orientation', 'P').upper()
        if orientation_attr not in ('P', 'PORTRAIT', 'L', 'LANDSCAPE'):
            orientation_attr = 'P'
        orientation = 'P' if orientation_attr.startswith('P') else 'L'
        
        page_size = getattr(template, 'page_size', 'A4').upper()
        
        primary_color_hex = getattr(getattr(template, 'branding', None), 'primary_color', '#000000')
        primary_color = _hex_to_rgb(primary_color_hex)
        company_name = getattr(getattr(template, 'branding', None), 'company_name', 'Company Name')
        footer_text = getattr(getattr(template, 'branding', None), 'footer_text', 'Confidential - Do not distribute')
        currency_symbol = getattr(getattr(template, 'locale', None), 'currency_symbol', '$')
        watermark_text = getattr(template, 'watermark_text', None)
        
        class ReportPDF(FPDF):
            def header(self):
                # Header with company name
                self.set_font('helvetica', 'B', 12)
                self.set_text_color(*primary_color)
                self.cell(0, 10, company_name, align='R')
                self.ln(15)
                
            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.set_text_color(128, 128, 128)
                # Page number
                self.cell(0, 10, f'Page {self.page_no()}', align='C')
                # Footer text
                self.set_x(self.l_margin)
                self.cell(0, 10, footer_text, align='L')
                
        pdf = ReportPDF(orientation=orientation, unit='mm', format=page_size)
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.add_page()
        
        # Cover Page
        pdf.set_font('helvetica', 'B', 24)
        pdf.set_text_color(*primary_color)
        title = getattr(calculator_config, 'title', 'Report')
        pdf.cell(0, 40, title, align='C', new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font('helvetica', '', 14)
        pdf.set_text_color(0, 0, 0)
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        pdf.cell(0, 10, f'Date: {date_str}', align='C', new_x="LMARGIN", new_y="NEXT")
        
        qr_code_url_pattern = getattr(template, 'qr_code_url_pattern', None)
        if qr_code_url_pattern and qrcode is not None:
            try:
                # Add QR code
                qr = qrcode.make(qr_code_url_pattern)
                img_byte_arr = io.BytesIO()
                qr.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                # place at center bottom
                pdf.image(img_byte_arr, x=pdf.w/2 - 20, y=150, w=40)
            except Exception:
                pass
                
        # Watermark
        if watermark_text:
            try:
                with pdf.local_context(text_color=(230, 230, 230)):
                    pdf.set_font("helvetica", "B", 60)
                    # Simple overlay for watermark
                    pdf.text(30, pdf.h/2, watermark_text)
            except Exception:
                pass
                
        pdf.add_page()
        
        def format_value(value: Any, format_type: str) -> str:
            if value is None:
                return ""
            if format_type == 'currency':
                return f"{currency_symbol}{float(value):,.2f}"
            elif format_type == 'percentage':
                return f"{float(value):.2f}%"
            elif isinstance(value, (int, float, Decimal)):
                return str(value)
            return str(value)
        
        # Summary Section
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(*primary_color)
        pdf.cell(0, 10, 'Summary', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('helvetica', '', 12)
        pdf.set_text_color(0, 0, 0)
        
        formulas = getattr(calculator_config, 'formulas', [])
        result_formulas = [f for f in formulas if getattr(f, 'is_result', False)]
        for f in result_formulas:
            f_id = getattr(f, 'id', '')
            f_label = getattr(f, 'label', f_id)
            f_format = getattr(f, 'format', 'default')
            val = results.get(f_id)
            formatted_val = format_value(val, f_format)
            pdf.cell(100, 10, f_label, border=1)
            pdf.cell(0, 10, formatted_val, border=1, align='R', new_x="LMARGIN", new_y="NEXT")
            
        pdf.ln(10)
        
        # Inputs Section
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(*primary_color)
        pdf.cell(0, 10, 'Inputs', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('helvetica', '', 12)
        pdf.set_text_color(0, 0, 0)
        
        inputs = getattr(calculator_config, 'inputs', [])
        for inp in inputs:
            inp_id = getattr(inp, 'id', '')
            inp_label = getattr(inp, 'label', inp_id)
            val = inputs_data.get(inp_id, '')
            pdf.cell(100, 10, inp_label, border=1)
            pdf.cell(0, 10, str(val), border=1, align='R', new_x="LMARGIN", new_y="NEXT")
            
        pdf.add_page()
        
        # Breakdown Section
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(*primary_color)
        pdf.cell(0, 10, 'Detailed Breakdown', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('helvetica', '', 12)
        pdf.set_text_color(0, 0, 0)
        
        for f in formulas:
            f_id = getattr(f, 'id', '')
            f_label = getattr(f, 'label', f_id)
            f_format = getattr(f, 'format', 'default')
            val = results.get(f_id)
            formatted_val = format_value(val, f_format)
            pdf.cell(100, 10, f_label, border=1)
            pdf.cell(0, 10, formatted_val, border=1, align='R', new_x="LMARGIN", new_y="NEXT")
            
        # Charts Section
        sections = getattr(template, 'sections', [])
        for section in sections:
            if getattr(section, 'type', '') == 'chart':
                pdf.add_page()
                pdf.set_font('helvetica', 'B', 16)
                pdf.set_text_color(*primary_color)
                chart_title = getattr(section, 'title', 'Chart')
                pdf.cell(0, 10, chart_title, new_x="LMARGIN", new_y="NEXT")
                
                try:
                    png_bytes = render_chart_to_png(section, results, calculator_config)
                    if png_bytes:
                        img_io = io.BytesIO(png_bytes)
                        pdf.image(img_io, x=15, w=pdf.w - 30)
                except Exception:
                    pdf.set_font('helvetica', 'I', 10)
                    pdf.set_text_color(128, 128, 128)
                    pdf.cell(0, 10, 'Chart rendering failed or not available.', new_x="LMARGIN", new_y="NEXT")
                    
        return bytes(pdf.output())
