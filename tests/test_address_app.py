"""
Gradio app để test so sánh địa chỉ
"""

import sys
import os

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from src.province_comparator import ProvinceComparator


# Khởi tạo comparator
data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tinh_thanh.json')
comparator = ProvinceComparator(data_path)


def compare_addresses(address1, address2):
    """
    So sánh 2 địa chỉ và trả về kết quả
    
    Args:
        address1: Địa chỉ 1
        address2: Địa chỉ 2
        
    Returns:
        Tuple (province1, province2, match_status, reason)
    """
    if not address1 or not address2:
        return "N/A", "N/A", "False", "Vui lòng nhập cả 2 địa chỉ"
    
    # Trích xuất tỉnh
    prov1 = comparator.extract_province(address1)
    prov2 = comparator.extract_province(address2)
    
    # So sánh
    is_match, reason = comparator.compare_provinces(prov1, prov2)
    
    # Format output
    province1_display = prov1 if prov1 else "N/A"
    province2_display = prov2 if prov2 else "N/A"
    match_display = "True" if is_match else "False"
    
    return province1_display, province2_display, match_display, reason


# Tạo Gradio interface
with gr.Blocks(title="Address Comparison Tester") as demo:
    gr.Markdown("# Address Comparison Tester")
    gr.Markdown("Nhập 2 địa chỉ để so sánh tỉnh/thành phố")
    
    with gr.Row():
        with gr.Column():
            address1_input = gr.Textbox(
                label="Address 1",
                placeholder="Nhập địa chỉ 1...",
                lines=2
            )
            address2_input = gr.Textbox(
                label="Address 2",
                placeholder="Nhập địa chỉ 2...",
                lines=2
            )
            
            submit_btn = gr.Button("So sánh", variant="primary", size="lg")
    
    with gr.Row():
        with gr.Column():
            province1_output = gr.Textbox(label="Province 1", interactive=False)
        with gr.Column():
            province2_output = gr.Textbox(label="Province 2", interactive=False)
    
    with gr.Row():
        match_output = gr.Textbox(label="Match", interactive=False)
    
    with gr.Row():
        reason_output = gr.Textbox(label="Reason", interactive=False, lines=2)
    
    # Kết nối button với function
    submit_btn.click(
        fn=compare_addresses,
        inputs=[address1_input, address2_input],
        outputs=[province1_output, province2_output, match_output, reason_output]
    )
    
    # Cho phép Enter để submit
    address1_input.submit(
        fn=compare_addresses,
        inputs=[address1_input, address2_input],
        outputs=[province1_output, province2_output, match_output, reason_output]
    )
    address2_input.submit(
        fn=compare_addresses,
        inputs=[address1_input, address2_input],
        outputs=[province1_output, province2_output, match_output, reason_output]
    )


if __name__ == "__main__":
    print(" Starting Address Comparison Tester...")
    demo.launch(server_name="127.0.0.1", server_port=7861, share=False, theme=gr.themes.Soft())
